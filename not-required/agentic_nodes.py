"""
Enhanced Agentic Nodes with Validation, Retry Logic, and Agent Collaboration
FIXED VERSION - Better error handling for None values
"""

from graph.agentic_state import AgenticState
from agents.head_meta_agent.head_agent import process_input as original_process_input, save_document
from agents.clinical_meta_agent.extraction_agent_enhanced import run_extraction_with_retry
from agents.clinical_meta_agent.summarizer_agent_enhanced import run_evidence_based_summarization
from agents.head_meta_agent.chat_agent_enhanced import run_chat
from agents.search_meta_agent.search_meta_agent import get_search_parameters, find_doctors
from agents.critic_agent.critic import CriticAgent, format_critique_report
from config.medical_validation import (
    validate_all_findings,
    check_missing_critical_metrics,
    detect_contradictions,
    detect_duplicates
)


def input_node(state: AgenticState) -> AgenticState:
    """
    Initial node: Processes input through Head Meta Agent
    """
    # Use enhanced chat for text inputs
    if state.get("input_type") == "text":
        from agents.head_meta_agent.stt_agent import run_stt_extraction
        text_input = state.get("text_input")
        patient_id = state.get("patient_id", "pt-001")
        
        # Use enhanced chat agent
        chat_response = run_chat(text_input, patient_id)
        state["final_response"] = chat_response
        state["next_step"] = "end"
        return state
    
    # For files, use original process
    return original_process_input(state)


def document_save_node(state: AgenticState) -> AgenticState:
    """
    Saves document to ChromaDB with confidence tracking
    """
    result = save_document(state)
    
    # Add confidence tracking
    if state.get("confidence"):
        if state["confidence"] < 0.7:
            if state.get("warnings") is None:
                state["warnings"] = []
            state["warnings"].append(
                "⚠️ Low OCR confidence may affect extraction accuracy"
            )
    
    return result


def extraction_with_validation_node(state: AgenticState) -> AgenticState:
    """
    Enhanced extraction node with critic validation and retry logic
    """
    print("\n=== EXTRACTION WITH VALIDATION ===")
    
    try:
        metadata = state.get("report_metadata")
        
        if not metadata:
            raise ValueError("No report metadata found")
        
        # Run extraction with retry mechanism
        max_retries = state.get("max_retries", 3)
        result = run_extraction_with_retry(metadata, max_retries=max_retries)
        
        # Safely extract values with defaults
        state["findings"] = result.get("findings", []) or []
        state["values"] = result.get("values", {}) or {}
        state["extraction_attempts"] = result.get("attempts", 1)
        state["extraction_critique"] = result.get("critique", {})
        
        # Safely get critique and confidence
        critique = result.get("critique") or {}
        state["extraction_confidence"] = critique.get("confidence", 0.0)
        
        # Store validation results
        state["validation_passed"] = result.get("success", False)
        state["critic_approved"] = critique.get("passed", False)
        
        # Initialize warnings if None
        if state.get("warnings") is None:
            state["warnings"] = []
        
        if not state["validation_passed"]:
            issues = critique.get("issues", [])
            if issues:
                state["warnings"].extend([issue.get("message", "Unknown issue") for issue in issues])
        
        # Check for missing critical metrics
        findings = state.get("findings") or []
        values = state.get("values") or {}
        
        missing_metrics = check_missing_critical_metrics(findings, values)
        state["missing_metrics"] = missing_metrics or []
        
        if missing_metrics:
            state["warnings"].append(
                f"⚠️ Missing {len(missing_metrics)} critical metrics"
            )
        
        # Check for duplicates
        duplicates = detect_duplicates(values)
        state["duplicates"] = duplicates or []
        
        if duplicates:
            state["warnings"].append(
                f"⚠️ {len(duplicates)} potential duplicate values detected"
            )
        
        print(f"Extraction completed: {len(findings)} findings, {len(values)} values")
        print(f"Validation passed: {state['validation_passed']}")
        print(f"Critic approved: {state['critic_approved']}")
        
        state["next_step"] = "validate_extraction"
        
    except Exception as e:
        print(f"Error in extraction: {e}")
        import traceback
        traceback.print_exc()
        state["error"] = str(e)
        state["next_step"] = "error"
    
    return state


def validate_extraction_node(state: AgenticState) -> AgenticState:
    """
    Validation checkpoint: Decides whether to retry or proceed
    """
    print("\n=== VALIDATION CHECKPOINT ===")
    
    critic_approved = state.get("critic_approved", False)
    validation_passed = state.get("validation_passed", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # If validation passed, proceed to summarization
    if critic_approved and validation_passed:
        print("✅ Validation passed - proceeding to summarization")
        state["next_step"] = "summarize"
        return state
    
    # If retries exhausted, proceed with warnings
    if retry_count >= max_retries:
        print("⚠️ Max retries reached - proceeding with warnings")
        state["next_step"] = "summarize"
        return state
    
    # Otherwise, retry extraction
    print(f"🔄 Validation failed - retrying (attempt {retry_count + 1}/{max_retries})")
    state["retry_count"] = retry_count + 1
    state["next_step"] = "extraction_with_validation"
    
    return state


def evidence_based_summarization_node(state: AgenticState) -> AgenticState:
    """
    Enhanced summarization with evidence backing and validation
    """
    print("\n=== EVIDENCE-BASED SUMMARIZATION ===")
    
    try:
        patient_id = state.get("patient_id", "pt-001")
        
        # Run evidence-based summarization
        result = run_evidence_based_summarization(patient_id)
        
        state["summary"] = result.get("summary", "")
        state["key_changes"] = result.get("key_changes", "")
        state["current_values"] = result.get("current_values", {})
        state["abnormal_values"] = result.get("abnormal_values", [])
        state["evidence_map"] = result.get("evidence_map", {})
        state["summary_confidence"] = result.get("confidence", "low")
        state["validation_results"] = result.get("validation_results", {})
        
        # Check for contradictions with previous reports
        current_values = state.get("current_values") or {}
        
        if len(current_values) > 0:
            from tools.summarizer_tools import get_all_findings
            reports = get_all_findings(patient_id)
            if len(reports) > 1:
                previous_values = reports[-2].get("values", {})
                
                contradictions = detect_contradictions(current_values, previous_values)
                state["contradictions"] = contradictions or []
                
                if contradictions:
                    if state.get("warnings") is None:
                        state["warnings"] = []
                    state["warnings"].append(
                        f"⚠️ {len(contradictions)} suspicious value changes detected"
                    )
        
        # Format final response
        final_response = format_final_response(state)
        state["final_response"] = final_response
        state["next_step"] = "end"
        
        print("✅ Evidence-based summary generated")
        
    except Exception as e:
        print(f"Error in summarization: {e}")
        import traceback
        traceback.print_exc()
        state["error"] = str(e)
        state["next_step"] = "error"
    
    return state


def search_with_refinement_node(state: AgenticState) -> AgenticState:
    """
    Enhanced search with clinical agent collaboration for refinement
    """
    print("\n=== SEARCH WITH REFINEMENT ===")
    
    try:
        # First attempt to get search parameters
        result = get_search_parameters(state)
        
        doctor_type = result.get("doctor_type")
        
        # If doctor type is unclear, request clinical agent feedback
        if doctor_type in ["Unknown", "Unable to determine", None]:
            print("🔄 Doctor type unclear - requesting clinical agent feedback")
            
            # Get clinical context
            patient_id = state.get("patient_id")
            from tools.summarizer_tools import get_all_findings
            reports = get_all_findings(patient_id)
            
            if reports:
                latest_findings = reports[-1].get("findings", [])
                latest_values = reports[-1].get("values", {})
                
                # Ask clinical agent for specialization refinement
                clinical_feedback = request_clinical_refinement(
                    latest_findings,
                    latest_values
                )
                
                state["clinical_feedback_to_search"] = clinical_feedback
                state["search_refinement_needed"] = True
                
                # Try again with clinical feedback
                from agents.search_meta_agent.location_and_search_term import run_search_term_and_location
                refined_result = run_search_term_and_location(
                    patient_id,
                    additional_context=clinical_feedback
                )
                
                state.update(refined_result)
            else:
                state["error"] = "Unable to determine doctor specialization"
                state["next_step"] = "error"
                return state
        
        state["next_step"] = "search_doctors"
        
    except Exception as e:
        print(f"Error in search refinement: {e}")
        import traceback
        traceback.print_exc()
        state["error"] = str(e)
        state["next_step"] = "error"
    
    return state


def request_clinical_refinement(findings: list, values: dict) -> str:
    """
    Request clinical agent to provide specialization refinement
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from config.settings import GOOGLE_API_KEY, LLM_MODEL
    import json
    
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )
    
    prompt = f"""
Based on the following clinical findings and lab values, determine the most appropriate 
medical subspecialization that the patient should see.

Findings: {json.dumps(findings)}
Values: {json.dumps(values)}

Be specific - provide subspecialty rather than general specialty.
For example:
- Instead of "Cardiologist", specify "Electrophysiologist" or "Interventional Cardiologist"
- Instead of "Gastroenterologist", specify "Hepatologist" or "Colorectal Specialist"

Return only the subspecialty name, nothing else.
"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        return content.strip()
    except Exception as e:
        print(f"Error getting clinical refinement: {e}")
        return "General Physician"


def doctor_search_node(state: AgenticState) -> AgenticState:
    """
    Execute doctor search with refined parameters
    """
    return find_doctors(state)


def error_node(state: AgenticState) -> AgenticState:
    """
    Enhanced error handling with detailed diagnostics
    """
    error_msg = state.get("error", "Unknown error occurred")
    warnings = state.get("warnings") or []
    
    error_response = "ERROR REPORT\n"
    error_response += "=" * 70 + "\n\n"
    error_response += f"❌ Error: {error_msg}\n\n"
    
    if warnings:
        error_response += "Warnings:\n"
        for warning in warnings:
            error_response += f"  {warning}\n"
        error_response += "\n"
    
    # Add diagnostics
    if state.get("extraction_attempts"):
        error_response += f"Extraction attempts: {state['extraction_attempts']}\n"
    
    if state.get("extraction_confidence"):
        error_response += f"Extraction confidence: {state['extraction_confidence']:.0%}\n"
    
    state["final_response"] = error_response
    state["next_step"] = "end"
    return state


def format_final_response(state: AgenticState) -> str:
    """
    Format comprehensive final response with all validation information
    """
    output = "COMPREHENSIVE MEDICAL REPORT ANALYSIS\n"
    output += "=" * 70 + "\n\n"
    
    # Confidence indicators
    extraction_conf = state.get("extraction_confidence", 0.0)
    summary_conf = state.get("summary_confidence", "unknown")
    
    output += "CONFIDENCE METRICS:\n"
    output += f"  OCR Confidence: {state.get('confidence', 0.0):.0%}\n"
    output += f"  Extraction Confidence: {extraction_conf:.0%}\n"
    output += f"  Summary Confidence: {summary_conf.upper()}\n"
    output += f"  Extraction Attempts: {state.get('extraction_attempts', 1)}\n"
    output += "\n"
    
    # Warnings
    warnings = state.get("warnings") or []
    if warnings:
        output += "⚠️ WARNINGS:\n"
        for warning in warnings:
            output += f"  {warning}\n"
        output += "\n"
    
    # Main summary
    output += state.get("summary", "No summary available")
    output += "\n\n"
    
    # Abnormal values
    abnormal_values = state.get("abnormal_values") or []
    if abnormal_values:
        output += "🔴 ABNORMAL VALUES REQUIRING ATTENTION:\n"
        output += "-" * 70 + "\n"
        for abnormal in abnormal_values:
            output += f"  • {abnormal.get('lab', 'Unknown')}: {abnormal.get('value', 'N/A')}\n"
            output += f"    Severity: {abnormal.get('severity', 'Unknown')}\n"
            output += f"    Reference: {abnormal.get('reference', 'N/A')}\n\n"
    
    # Key changes
    output += "KEY CHANGES:\n"
    output += "-" * 70 + "\n"
    output += state.get("key_changes", "No changes detected")
    output += "\n\n"
    
    # Contradictions
    contradictions = state.get("contradictions") or []
    if contradictions:
        output += "⚠️ SUSPICIOUS CHANGES DETECTED:\n"
        output += "-" * 70 + "\n"
        for contra in contradictions:
            output += f"  • {contra.get('lab', 'Unknown')}: "
            output += f"{contra.get('previous_value', 'N/A')} → {contra.get('current_value', 'N/A')}\n"
            output += f"    {contra.get('message', '')}\n\n"
    
    # Current values
    output += "CURRENT VALUES:\n"
    output += "-" * 70 + "\n"
    current_values = state.get("current_values") or {}
    validation_results = (state.get("validation_results") or {}).get("validation_results", {})
    
    for param, value in current_values.items():
        flag = ""
        if param in validation_results:
            val_result = validation_results[param]
            if val_result.get("flag"):
                flag = f" {val_result.get('severity_label', '')}"
        
        output += f"  {param}: {value}{flag}\n"
    
    output += "\n"
    
    # Missing metrics
    missing_metrics = state.get("missing_metrics") or []
    if missing_metrics:
        output += "⚠️ POTENTIALLY MISSING METRICS:\n"
        output += "-" * 70 + "\n"
        for metric in missing_metrics:
            output += f"  • {metric.get('message', 'Unknown')}\n"
        output += "\n"
    
    return output


# Routing functions
def route_after_validation(state: AgenticState) -> str:
    """
    Route based on validation results
    """
    if state.get("next_step") == "summarize":
        return "summarize"
    elif state.get("next_step") == "extraction_with_validation":
        return "extraction_retry"
    else:
        return state.get("next_step", "error")


def route_next_step(state: AgenticState) -> str:
    """
    General routing function
    """
    return state.get("next_step", "end")
"""
Enhanced Agentic Workflow with Conditional Loops and Validation
True agent-based execution with retry mechanisms and inter-agent collaboration
"""

from langgraph.graph import StateGraph, END
from graph.agentic_state import AgenticState
from graph.agentic_nodes import (
    input_node,
    document_save_node,
    extraction_with_validation_node,
    validate_extraction_node,
    evidence_based_summarization_node,
    search_with_refinement_node,
    doctor_search_node,
    error_node,
    route_after_validation,
    route_next_step
)


def create_agentic_report_workflow():
    """
    Creates the enhanced agentic workflow with validation loops
    
    Features:
    - Critic agent feedback loops
    - Retry mechanisms with validation
    - Evidence-based outputs
    - Confidence thresholds
    - Agent-to-agent collaboration
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(AgenticState)
    
    # Add nodes
    workflow.add_node("input_processing", input_node)
    workflow.add_node("save_document", document_save_node)
    workflow.add_node("extraction_with_validation", extraction_with_validation_node)
    workflow.add_node("validate_extraction", validate_extraction_node)
    workflow.add_node("summarize_with_evidence", evidence_based_summarization_node)
    workflow.add_node("error", error_node)
    
    # Set entry point
    workflow.set_entry_point("input_processing")
    
    # Define edges with conditional routing
    
    # From input processing
    workflow.add_conditional_edges(
        "input_processing",
        route_next_step,
        {
            "save_document": "save_document",
            "error": "error",
            "end": END
        }
    )
    
    # From document save
    workflow.add_conditional_edges(
        "save_document",
        route_next_step,
        {
            "extract_findings": "extraction_with_validation",  # Route to enhanced extraction
            "error": "error",
            "end": END
        }
    )
    
    # From extraction - always goes to validation checkpoint
    workflow.add_conditional_edges(
        "extraction_with_validation",
        route_next_step,
        {
            "validate_extraction": "validate_extraction",
            "error": "error"
        }
    )
    
    # Validation checkpoint - can loop back or proceed
    workflow.add_conditional_edges(
        "validate_extraction",
        route_after_validation,
        {
            "extraction_retry": "extraction_with_validation",  # Retry loop
            "summarize": "summarize_with_evidence",           # Proceed
            "error": "error"
        }
    )
    
    # From summarization
    workflow.add_conditional_edges(
        "summarize_with_evidence",
        route_next_step,
        {
            "end": END,
            "error": "error"
        }
    )
    
    # Error handling
    workflow.add_edge("error", END)
    
    app = workflow.compile()
    
    return app


def create_agentic_search_workflow():
    """
    Creates the enhanced agentic search workflow with refinement
    
    Features:
    - Agent-to-agent collaboration (Search ↔ Clinical)
    - Automatic refinement when specialization is unclear
    - Context-aware doctor recommendations
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(AgenticState)
    
    # Add nodes
    workflow.add_node("search_with_refinement", search_with_refinement_node)
    workflow.add_node("search_doctors", doctor_search_node)
    workflow.add_node("error", error_node)
    
    # Set entry point
    workflow.set_entry_point("search_with_refinement")
    
    # Define edges
    workflow.add_conditional_edges(
        "search_with_refinement",
        route_next_step,
        {
            "search_doctors": "search_doctors",
            "error": "error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "search_doctors",
        route_next_step,
        {
            "end": END,
            "error": "error"
        }
    )
    
    workflow.add_edge("error", END)
    
    app = workflow.compile()
    
    return app


def run_agentic_report_workflow(
    input_type: str,
    file_path: str = None,
    text_input: str = None,
    patient_id: str = "pt-001",
    max_retries: int = 3
) -> dict:
    """
    Runs the complete agentic report processing workflow
    
    Args:
        input_type: Type of input ("pdf", "image", "audio", "text")
        file_path: Path to file (for pdf, image, audio)
        text_input: Text input (for text type)
        patient_id: Patient identifier
        max_retries: Maximum number of extraction retry attempts
        
    Returns:
        Final state dictionary with comprehensive results
    """
    initial_state = {
        "input_type": input_type,
        "file_path": file_path,
        "text_input": text_input,
        "patient_id": patient_id,
        "max_retries": max_retries,
        
        # Initialize all fields
        "extracted_text": None,
        "confidence": None,
        "report_metadata": None,
        
        "findings": None,
        "values": None,
        "extraction_attempts": 0,
        "extraction_critique": None,
        "extraction_confidence": None,
        
        "summary": None,
        "key_changes": None,
        "current_values": None,
        "abnormal_values": None,
        "evidence_map": None,
        "summary_confidence": None,
        
        "validation_results": None,
        "missing_metrics": None,
        "contradictions": None,
        "duplicates": None,
        
        "doctor_type": None,
        "location": None,
        "search_params": None,
        "search_results": None,
        "top_doctors": None,
        "total_results": None,
        "search_refinement_needed": None,
        "raw_search_output": None,
        
        "clinical_feedback_to_search": None,
        "search_refinement_request": None,
        
        "final_response": None,
        
        "error": None,
        "warnings": None,
        "should_retry": None,
        "retry_count": 0,
        
        "next_step": None,
        "validation_passed": None,
        "critic_approved": None
    }
    
    app = create_agentic_report_workflow()
    result = app.invoke(initial_state)
    
    return result


def run_agentic_search_workflow(patient_id: str) -> dict:
    """
    Runs the agentic doctor search workflow with refinement
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Final state dictionary with search results
    """
    initial_state = {
        "input_type": None,
        "file_path": None,
        "text_input": None,
        "patient_id": patient_id,
        "max_retries": 3,
        
        "extracted_text": None,
        "confidence": None,
        "report_metadata": None,
        
        "findings": None,
        "values": None,
        "extraction_attempts": 0,
        "extraction_critique": None,
        "extraction_confidence": None,
        
        "summary": None,
        "key_changes": None,
        "current_values": None,
        "abnormal_values": None,
        "evidence_map": None,
        "summary_confidence": None,
        
        "validation_results": None,
        "missing_metrics": None,
        "contradictions": None,
        "duplicates": None,
        
        "doctor_type": None,
        "location": None,
        "search_params": None,
        "search_results": None,
        "top_doctors": None,
        "total_results": None,
        "search_refinement_needed": None,
        "raw_search_output": None,
        
        "clinical_feedback_to_search": None,
        "search_refinement_request": None,
        
        "final_response": None,
        
        "error": None,
        "warnings": None,
        "should_retry": None,
        "retry_count": 0,
        
        "next_step": None,
        "validation_passed": None,
        "critic_approved": None
    }
    
    app = create_agentic_search_workflow()
    result = app.invoke(initial_state)
    
    return result


# Convenience function to check workflow status
def get_workflow_status(state: AgenticState) -> dict:
    """
    Get current workflow status and metrics
    
    Args:
        state: Current workflow state
        
    Returns:
        Status dictionary
    """
    return {
        "current_step": state.get("next_step", "unknown"),
        "extraction_attempts": state.get("extraction_attempts", 0),
        "validation_passed": state.get("validation_passed", False),
        "critic_approved": state.get("critic_approved", False),
        "extraction_confidence": state.get("extraction_confidence", 0.0),
        "summary_confidence": state.get("summary_confidence", "unknown"),
        "warnings_count": len(state.get("warnings", [])),
        "has_error": state.get("error") is not None,
        "abnormal_values_count": len(state.get("abnormal_values", [])),
        "missing_metrics_count": len(state.get("missing_metrics", [])),
        "contradictions_count": len(state.get("contradictions", []))
    }

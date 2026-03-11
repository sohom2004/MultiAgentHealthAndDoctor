"""
Enhanced Chat Agent with Confidence Thresholds and Dynamic Tool Triggering
"""

from langchain.agents import initialize_agent, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.chat_tools import query_findings, get_patient_history
from config.settings import GOOGLE_API_KEY, LLM_MODEL
from agents.clinical_meta_agent.extraction_agent_enhanced import run_extraction_with_retry
from agents.clinical_meta_agent.summarizer_agent_enhanced import run_evidence_based_summarization
import json


# Confidence threshold for retrieval
RETRIEVAL_CONFIDENCE_THRESHOLD = 0.6


def query_findings_with_confidence(action_input: str) -> str:
    """
    Enhanced query with confidence scoring
    
    Args:
        action_input: Query string in format "query|patient_id"
        
    Returns:
        Results with confidence scores
    """
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from config.settings import CHROMA_DIR, EMBEDDING_MODEL, FINDINGS_COLLECTION
    
    try:
        if '|' in action_input:
            query, patient_id = action_input.split('|', 1)
        else:
            query = action_input
            patient_id = "pt-001"
        
        query = query.strip()
        patient_id = patient_id.strip()
        
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vector_store = Chroma(
            collection_name=FINDINGS_COLLECTION,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR)
        )
        
        # Get results with similarity scores
        results = vector_store.similarity_search_with_score(
            query,
            k=5,
            filter={"patient_id": patient_id}
        )
        
        if not results:
            return json.dumps({
                "status": "no_results",
                "message": f"No findings found for patient {patient_id} matching query: {query}",
                "confidence": 0.0
            })
        
        # Calculate average confidence (similarity score)
        # Note: ChromaDB returns distance, lower is better
        # Convert to similarity: 1 / (1 + distance)
        scores = [1 / (1 + score) for _, score in results]
        avg_confidence = sum(scores) / len(scores)
        
        # Check confidence threshold
        if avg_confidence < RETRIEVAL_CONFIDENCE_THRESHOLD:
            return json.dumps({
                "status": "low_confidence",
                "message": "⚠️ Not enough context to answer confidently. Please provide more specific information or rephrase your question.",
                "confidence": avg_confidence,
                "available_data": "Limited matching information in medical history"
            })
        
        # Format results with confidence
        formatted_results = []
        for i, (doc, score) in enumerate(results, 1):
            confidence = 1 / (1 + score)
            try:
                content = json.loads(doc.page_content)
                findings = content.get("findings", [])
                values = content.get("values", {})
                
                result_text = {
                    "index": i,
                    "confidence": confidence,
                    "date": doc.metadata.get('report_date', 'Unknown'),
                    "findings": findings,
                    "values": values
                }
                
                formatted_results.append(result_text)
            except:
                formatted_results.append({
                    "index": i,
                    "confidence": confidence,
                    "raw_content": doc.page_content
                })
        
        return json.dumps({
            "status": "success",
            "confidence": avg_confidence,
            "results": formatted_results,
            "message": f"Found {len(results)} relevant findings with {avg_confidence:.0%} confidence"
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error querying findings: {str(e)}",
            "confidence": 0.0
        })


def trigger_clinical_workflow(action_input: str) -> str:
    """
    Dynamically trigger clinical workflows (extraction, summarization, trend analysis)
    
    Args:
        action_input: Command string like "summarize|patient_id" or "trends|patient_id|lab_name"
        
    Returns:
        Workflow results
    """
    try:
        parts = action_input.split('|')
        command = parts[0].strip().lower()
        
        if command == "summarize" and len(parts) >= 2:
            patient_id = parts[1].strip()
            result = run_evidence_based_summarization(patient_id)
            return json.dumps({
                "status": "success",
                "command": "summarize",
                "result": result
            })
        
        elif command == "trends" and len(parts) >= 3:
            patient_id = parts[1].strip()
            lab_name = parts[2].strip()
            result = analyze_lab_trends(patient_id, lab_name)
            return json.dumps({
                "status": "success",
                "command": "trends",
                "result": result
            })
        
        elif command == "compare" and len(parts) >= 3:
            patient_id = parts[1].strip()
            date1 = parts[2].strip() if len(parts) > 2 else None
            date2 = parts[3].strip() if len(parts) > 3 else None
            result = compare_reports(patient_id, date1, date2)
            return json.dumps({
                "status": "success",
                "command": "compare",
                "result": result
            })
        
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unknown workflow command: {command}"
            })
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error executing workflow: {str(e)}"
        })


def analyze_lab_trends(patient_id: str, lab_name: str) -> dict:
    """
    Analyze trends for a specific lab value over time
    """
    from tools.summarizer_tools import get_all_findings
    from config.medical_validation import normalize_lab_name, extract_numeric_value
    
    reports = get_all_findings(patient_id)
    
    if not reports:
        return {"error": "No reports found"}
    
    normalized_lab = normalize_lab_name(lab_name)
    trend_data = []
    
    for report in reports:
        values = report.get("values", {})
        for lab, value in values.items():
            if normalize_lab_name(lab) == normalized_lab:
                numeric_val = extract_numeric_value(value)
                if numeric_val:
                    trend_data.append({
                        "date": report.get("report_date", "Unknown"),
                        "value": numeric_val,
                        "raw_value": value
                    })
    
    if not trend_data:
        return {"error": f"No data found for {lab_name}"}
    
    # Sort by date
    trend_data.sort(key=lambda x: x["date"])
    
    # Calculate trend
    if len(trend_data) >= 2:
        first_val = trend_data[0]["value"]
        last_val = trend_data[-1]["value"]
        change = last_val - first_val
        percent_change = (change / first_val * 100) if first_val != 0 else 0
        
        trend_direction = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
    else:
        trend_direction = "insufficient data"
        percent_change = 0
    
    return {
        "lab_name": lab_name,
        "data_points": len(trend_data),
        "trend": trend_direction,
        "percent_change": percent_change,
        "history": trend_data
    }


def compare_reports(patient_id: str, date1: str = None, date2: str = None) -> dict:
    """
    Compare two reports or latest with previous
    """
    from tools.summarizer_tools import get_all_findings
    from config.medical_validation import detect_contradictions
    
    reports = get_all_findings(patient_id)
    
    if len(reports) < 2:
        return {"error": "Need at least 2 reports to compare"}
    
    # If dates not specified, compare latest two
    if not date1 or not date2:
        report1 = reports[-2]
        report2 = reports[-1]
    else:
        # Find reports by date
        report1 = next((r for r in reports if r.get("report_date") == date1), None)
        report2 = next((r for r in reports if r.get("report_date") == date2), None)
        
        if not report1 or not report2:
            return {"error": "Could not find reports for specified dates"}
    
    values1 = report1.get("values", {})
    values2 = report2.get("values", {})
    
    # Detect changes and contradictions
    contradictions = detect_contradictions(values2, values1)
    
    changes = []
    for lab, val2 in values2.items():
        if lab in values1:
            from config.medical_validation import extract_numeric_value
            num1 = extract_numeric_value(values1[lab])
            num2 = extract_numeric_value(val2)
            
            if num1 and num2 and num1 != num2:
                change_percent = ((num2 - num1) / num1 * 100) if num1 != 0 else 0
                changes.append({
                    "lab": lab,
                    "previous": values1[lab],
                    "current": val2,
                    "change_percent": change_percent
                })
    
    return {
        "report1_date": report1.get("report_date", "Unknown"),
        "report2_date": report2.get("report_date", "Unknown"),
        "changes": changes,
        "contradictions": contradictions,
        "new_values": [lab for lab in values2 if lab not in values1],
        "removed_values": [lab for lab in values1 if lab not in values2]
    }


def create_enhanced_chat_agent():
    """
    Creates an enhanced chat agent with confidence-based retrieval and dynamic workflows
    """
    tools = [
        Tool(
            name="QueryFindingsWithConfidence",
            func=query_findings_with_confidence,
            description=(
                "Search patient findings using semantic search with confidence scoring. "
                "Input: 'query|patient_id'. Returns results only if confidence is above threshold. "
                "Use this for answering questions about patient's medical history."
            )
        ),
        Tool(
            name="GetPatientHistory",
            func=get_patient_history,
            description=(
                "Get complete patient report history. Input: patient_id as string. "
                "Use this for comprehensive history overview."
            )
        ),
        Tool(
            name="TriggerClinicalWorkflow",
            func=trigger_clinical_workflow,
            description=(
                "Trigger clinical workflows like summarization or trend analysis. "
                "Commands: 'summarize|patient_id', 'trends|patient_id|lab_name', "
                "'compare|patient_id|date1|date2'. Use when user asks for summary, "
                "trends over time, or comparison between reports."
            )
        )
    ]
    
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.7
    )
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent


def run_enhanced_chat(query: str, patient_id: str) -> str:
    """
    Runs the enhanced chat agent with confidence-based responses
    
    Args:
        query: User query
        patient_id: Patient identifier
        
    Returns:
        Agent response
    """
    agent = create_enhanced_chat_agent()
    
    # Detect intent
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["summarize", "summary", "overview"]):
        workflow_hint = "Use TriggerClinicalWorkflow with 'summarize' command"
    elif any(word in query_lower for word in ["trend", "over time", "progression", "history of"]):
        workflow_hint = "Use TriggerClinicalWorkflow with 'trends' command"
    elif any(word in query_lower for word in ["compare", "difference", "vs", "versus"]):
        workflow_hint = "Use TriggerClinicalWorkflow with 'compare' command"
    else:
        workflow_hint = "Use QueryFindingsWithConfidence for specific questions"
    
    prompt = f"""
You are a helpful medical assistant chatbot with confidence-aware responses.

User query: {query}
Patient ID: {patient_id}

IMPORTANT RULES:
1. Only state facts that are supported by retrieved data
2. If confidence is low, acknowledge uncertainty and ask for clarification
3. Dynamically trigger workflows when appropriate (summaries, trends, comparisons)
4. Be conversational but precise
5. Always prioritize patient safety

Suggestion: {workflow_hint}

Respond to the user's query using the appropriate tools.
"""
    
    try:
        response = agent.invoke({"input": prompt})
        output = response.get("output", "I'm sorry, I couldn't process that query.")
        
        # Check if output contains low confidence warning
        if isinstance(output, str) and "low_confidence" in output.lower():
            return ("⚠️ I don't have enough information in the medical records to answer "
                   "that question confidently. Could you rephrase or provide more context?")
        
        return output
        
    except Exception as e:
        return f"I encountered an error processing your request: {str(e)}"


def run_chat(query: str, patient_id: str) -> str:
    """
    Main entry point for chat functionality
    """
    return run_enhanced_chat(query, patient_id)
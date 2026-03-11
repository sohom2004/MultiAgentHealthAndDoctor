from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import (
    input_node,
    extraction_node,
    summarization_node,
    search_params_node,
    doctor_search_node,
    search_error_node,
    error_node,
    route_next_step
)


def create_report_workflow():
    """
    Creates the LangGraph workflow for report processing and summarization.
    OCR text flows directly from input_processing into extract_findings via state.
    
    Returns:
        Compiled LangGraph workflow for report processing
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("input_processing", input_node)
    workflow.add_node("extract_findings", extraction_node)
    workflow.add_node("summarize", summarization_node)
    workflow.add_node("error", error_node)
    
    workflow.set_entry_point("input_processing")
    
    # input_processing routes directly to extract_findings (pdf/image)
    # or END (text/audio chat), or error
    workflow.add_conditional_edges(
        "input_processing",
        route_next_step,
        {
            "extract_findings": "extract_findings",
            "error": "error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "extract_findings",
        route_next_step,
        {
            "summarize": "summarize",
            "error": "error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "summarize",
        route_next_step,
        {
            "end": END,
            "error": "error"
        }
    )
    
    workflow.add_edge("error", END)
    
    app = workflow.compile()
    
    return app


def create_search_workflow():
    """
    Creates the LangGraph workflow for doctor search
    
    Returns:
        Compiled LangGraph workflow for doctor search
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("get_search_params", search_params_node)
    workflow.add_node("search_doctors", doctor_search_node)
    workflow.add_node("search_error", search_error_node)
    
    workflow.set_entry_point("get_search_params")
    
    workflow.add_conditional_edges(
        "get_search_params",
        route_next_step,
        {
            "search_doctors": "search_doctors",
            "error": "search_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "search_doctors",
        route_next_step,
        {
            "end": END,
            "error": "search_error"
        }
    )
    
    workflow.add_edge("search_error", END)
    
    app = workflow.compile()
    
    return app


def run_report_workflow(
    input_type: str,
    file_path: str = None,
    text_input: str = None,
    patient_id: str = "pt-001" 
) -> dict:
    """
    Runs the complete report processing and summarization workflow
    
    Args:
        input_type: Type of input ("pdf", "image", "audio", "text")
        file_path: Path to file (for pdf, image, audio)
        text_input: Text input (for text type)
        patient_id: Patient identifier
        
    Returns:
        Final state dictionary with report summary
    """
    initial_state = {
        "input_type": input_type,
        "file_path": file_path,
        "text_input": text_input,
        "patient_id": patient_id,
        "extracted_text": None,
        "confidence": None,
        "report_metadata": None,
        "findings": None,
        "values": None,
        "summary": None,
        "key_changes": None,
        "current_values": None,
        "doctor_type": None,
        "location": None,
        "search_results": None,
        "top_doctors": None,
        "total_results": None,
        "raw_search_output": None,
        "final_response": None,
        "error": None,
        "next_step": None
    }
    
    app = create_report_workflow()
    result = app.invoke(initial_state)
    
    return result


def run_search_workflow(patient_id: str) -> dict:
    """
    Runs the doctor search workflow independently
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Final state dictionary with doctor search results
    """
    initial_state = {
        "input_type": None,
        "file_path": None,
        "text_input": None,
        "patient_id": patient_id,
        "extracted_text": None,
        "confidence": None,
        "report_metadata": None,
        "findings": None,
        "values": None,
        "summary": None,
        "key_changes": None,
        "current_values": None,
        "doctor_type": None,
        "location": None,
        "search_params": None,
        "search_results": None,
        "top_doctors": None,
        "total_results": None,
        "raw_search_output": None,
        "final_response": None,
        "error": None,
        "next_step": None
    }
    
    app = create_search_workflow()
    result = app.invoke(initial_state)
    
    return result
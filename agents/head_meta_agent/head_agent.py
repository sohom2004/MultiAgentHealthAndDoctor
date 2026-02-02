from agents.head_meta_agent.ocr_agent import run_ocr_extraction
from agents.head_meta_agent.stt_agent import run_stt_extraction
from agents.head_meta_agent.document_save_agent import run_document_save
from agents.head_meta_agent.chat_agent import run_chat
from graph.state import AgentState


def process_input(state: AgentState) -> AgentState:
    """
    Head Meta Agent: Processes input based on type
    Routes to OCR, STT, Chat, or uses text directly
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with extracted text or chat response
    """
    print("\n=== HEAD META AGENT: Processing Input ===")
    
    input_type = state.get("input_type")
    file_path = state.get("file_path")
    text_input = state.get("text_input")
    
    try:
        if input_type in ["pdf", "image"]:
            print(f"Processing {input_type} file: {file_path}")
            result = run_ocr_extraction(file_path)
            state["extracted_text"] = result.get("content", "")
            state["confidence"] = result.get("confidence", 0.0)
            state["next_step"] = "save_document"
            
        elif input_type == "audio":
            print(f"Processing audio file: {file_path}")
            text_input = run_stt_extraction(file_path)
            state["extracted_text"] = text_input
            state["confidence"] = 1.0
            print("Processing as conversational query")
            patient_id = state.get("patient_id", "pt-001")
            chat_response = run_chat(text_input, patient_id)
            state["final_response"] = chat_response
            state["next_step"] = "end"
            
        elif input_type == "text":
            print("Processing as conversational query")
            patient_id = state.get("patient_id", "pt-001")
            chat_response = run_chat(text_input, patient_id)
            state["final_response"] = chat_response
            state["next_step"] = "end"
        else:
            raise ValueError(f"Unknown input type: {input_type}")
        
    except Exception as e:
        print(f"Error in Head Meta Agent: {e}")
        state["error"] = str(e)
        state["next_step"] = "error"
    
    return state


def save_document(state: AgentState) -> AgentState:
    """
    Saves the extracted document to ChromaDB
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with metadata
    """
    print("\n=== HEAD META AGENT: Saving Document ===")
    
    try:
        text_data = {
            "content": state.get("extracted_text", ""),
            "confidence": state.get("confidence", 0.0)
        }
        
        patient_id = state.get("patient_id", "pt-1")
        
        metadata = run_document_save(text_data, patient_id)
        state["report_metadata"] = metadata
        
        print(f"Document saved with metadata: {metadata}")
        state["next_step"] = "extract_findings"
        
    except Exception as e:
        print(f"Error saving document: {e}")
        state["error"] = str(e)
        state["next_step"] = "error"
    
    return state
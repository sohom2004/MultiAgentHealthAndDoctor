from agents.clinical_meta_agent.extraction_agent import run_extraction
from agents.clinical_meta_agent.summarizer_agent import run_summarization
from graph.state import AgentState


def extract_findings(state: AgentState) -> AgentState:
    """
    Clinical Meta Agent: Extracts findings from OCR text in state.

    Args:
        state: Current agent state

    Returns:
        Updated state with findings, values, and report_metadata
    """
    print("\n=== CLINICAL META AGENT: Extracting Findings ===")

    try:
        ocr_text = state.get("extracted_text", "")
        patient_id = state.get("patient_id", "pt-001")

        if not ocr_text:
            raise ValueError("No extracted text found in state")

        result = run_extraction(ocr_text, patient_id)

        state["findings"] = result.get("findings", [])
        state["values"] = result.get("values", {})
        state["report_metadata"] = result.get("metadata", {})

        print(f"Extracted {len(state['findings'])} findings")
        state["next_step"] = "summarize"

    except Exception as e:
        print(f"Error extracting findings: {e}")
        state["error"] = str(e)
        state["next_step"] = "error"

    return state


def summarize_report(state: AgentState) -> AgentState:
    """
    Clinical Meta Agent: Generates summary from findings

    Args:
        state: Current agent state

    Returns:
        Updated state with summary
    """
    print("\n=== CLINICAL META AGENT: Generating Summary ===")

    try:
        patient_id = state.get("patient_id", "pt-1")

        summary_result = run_summarization(patient_id)

        state["summary"] = summary_result.get("summary", "")
        state["key_changes"] = summary_result.get("key_changes", "")
        state["current_values"] = summary_result.get("current_values", {})

        final_response = f"""
MEDICAL REPORT SUMMARY
{'='*50}

{state['summary']}

KEY CHANGES:
{state['key_changes']}

CURRENT VALUES:
{state['current_values']}
"""

        state["final_response"] = final_response
        state["next_step"] = "end"

        print("Summary generated successfully")

    except Exception as e:
        print(f"Error generating summary: {e}")
        state["error"] = str(e)
        state["next_step"] = "error"

    return state
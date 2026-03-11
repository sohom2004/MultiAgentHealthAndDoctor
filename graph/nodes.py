from graph.state import AgentState
from agents.head_meta_agent.head_agent import process_input
from agents.clinical_meta_agent.clinical_agent import extract_findings, summarize_report
from agents.search_meta_agent.search_meta_agent import get_search_parameters, find_doctors, handle_search_error


def input_node(state: AgentState) -> AgentState:
    """
    Initial node: Processes input through Head Meta Agent
    """
    return process_input(state)


def extraction_node(state: AgentState) -> AgentState:
    """
    Extracts findings through Clinical Meta Agent.
    Reads extracted_text and patient_id directly from state.
    """
    return extract_findings(state)


def summarization_node(state: AgentState) -> AgentState:
    """
    Generates summary through Clinical Meta Agent
    """
    return summarize_report(state)

def search_params_node(state: AgentState) -> AgentState:
    """
    Gets search parameters (doctor type and location) through Search Meta Agent
    """
    return get_search_parameters(state)


def doctor_search_node(state: AgentState) -> AgentState:
    """
    Searches for doctors through Search Meta Agent
    """
    return find_doctors(state)

def search_error_node(state: AgentState) -> AgentState:
    """
    Handles search-specific errors through Search Meta Agent
    """
    return handle_search_error(state)

def error_node(state: AgentState) -> AgentState:
    """
    Handles errors
    """
    error_msg = state.get("error", "Unknown error occurred")
    state["final_response"] = f"ERROR: {error_msg}"
    state["next_step"] = "end"
    return state


def route_next_step(state: AgentState) -> str:
    """
    Routes to the next node based on state
    """
    next_step = state.get("next_step", "end")
    return next_step
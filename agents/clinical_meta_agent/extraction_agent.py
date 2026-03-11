from langchain.agents import initialize_agent, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.extraction_tools import save_findings
from config.settings import GOOGLE_API_KEY, LLM_MODEL


def create_extraction_agent():
    """
    Creates an extraction agent for extracting medical findings from OCR text.

    Returns:
        LangChain agent
    """
    tools = [
        Tool(
            name="saveFindings",
            func=save_findings,
            description=(
                "Saves extracted findings, values, and patient_id to the vector database. "
                "Input must be a dict (or valid JSON string) with keys: "
                "'findings' (list), 'values' (dict), 'patient_id' (string). "
                "Metadata (report_id, upload_date) is generated automatically. "
                "Returns a JSON string of the saved metadata."
            )
        )
    ]

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY
    )

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True
    )

    return agent


def run_extraction(ocr_text: str, patient_id: str) -> dict:
    """
    Runs the extraction agent to extract findings from OCR text and save them.

    Args:
        ocr_text:   Raw text extracted by the OCR agent (from agent state)
        patient_id: Patient identifier (from agent state)

    Returns:
        Dictionary with 'findings', 'values', and saved 'metadata'
    """
    agent = create_extraction_agent()

    prompt = f"""
    You are a medical information extraction agent. Perform the following steps:

    1. Analyse the report text below and identify important clinical information.
    2. Extract:
       - findings: a list of the key observations about the patient's condition
       - values:   a dict of critical measurements or data points with their values
    3. Call saveFindings with a dict containing:
       {{
         "findings": <extracted findings list>,
         "values":   <extracted values dict>,
         "patient_id": "{patient_id}"
       }}
       Do NOT include a 'metadata' key — it is generated automatically.
    4. Return the final output as a dict with keys 'findings', 'values', and 'metadata'
       (use the metadata string returned by saveFindings).

    Report text:
    {ocr_text}
    """

    response = agent.invoke({"input": prompt})
    output = response.get("output", "")

    try:
        import ast
        result = ast.literal_eval(output)
        return result
    except Exception:
        return {"findings": [], "values": {}, "metadata": {}}
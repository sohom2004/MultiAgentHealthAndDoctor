from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from tools.summarizer_tools import get_all_findings, store_summaries
from config.settings import GOOGLE_API_KEY, LLM_MODEL
import json
import re


def clean_json_response(content: str) -> str:
    """
    Cleans JSON response by removing markdown code blocks and extra text
    
    Args:
        content: Raw LLM response
        
    Returns:
        Clean JSON string
    """
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        parts = content.split('```')
        for part in parts:
            if '{' in part and '}' in part:
                content = part.strip()
                break
    
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        content = json_match.group(0)
    
    return content


def create_summarizer_agent():
    """
    Creates a summarizer chain for generating medical summaries
    
    Returns:
        LangChain chain
    """
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3
    )
    
    prompt = PromptTemplate(
        input_variables=["latest", "history"],
        template="""
You are a medical summarization agent. Analyze the patient's medical reports and provide a comprehensive summary.

Latest findings and values:
{latest}

Past reports (for context):
{history}

IMPORTANT: You must respond with ONLY a valid JSON object. Do not include markdown code blocks, explanations, or any text outside the JSON.

Return this exact JSON structure:
{{
  "summary": "A clear, concise summary of the patient's current medical condition based on the latest report. Include key findings and any notable observations.",
  "key_changes": "Comparison with previous reports. Mention improvements, deteriorations, or stable conditions. If this is the first report, state 'This is the first report on file.'",
  "current_values": {{
    "parameter_name": "value with unit",
    "another_parameter": "value with unit"
  }}
}}

Make sure current_values contains ALL important medical values from the latest report with their units.
"""
    )
    
    summarizer_chain = prompt | llm
    return summarizer_chain


def run_summarization(patient_id: str) -> dict:
    """
    Runs the summarizer to generate a patient summary
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Dictionary with summary, key_changes, and current_values
    """
    reports = get_all_findings(patient_id)
    
    if not reports:
        return {
            "summary": "No stored findings for this patient.",
            "key_changes": "N/A",
            "current_values": {}
        }
    
    latest = reports[-1]
    history = reports[:-1] if len(reports) > 1 else []
    
    summarizer = create_summarizer_agent()
    response = summarizer.invoke({
        "latest": json.dumps(latest),
        "history": json.dumps(history)
    })
    
    try:
        content = response.content if hasattr(response, 'content') else str(response)
        
        content = clean_json_response(content)
        
        result = json.loads(content)
        
        summary_text = f"""MEDICAL REPORT SUMMARY
        ==================================================

        {result.get('summary', 'No summary available')}

        KEY CHANGES:
        {result.get('key_changes', 'No changes detected')}

        CURRENT VALUES:
        {json.dumps(result.get('current_values', {}), indent=2)}
        """
        
        # Pass the formatted string instead of the dict
        store_summaries(summary_text, patient_id)
        
        return {
            "summary": result.get("summary", "No summary available"),
            "key_changes": result.get("key_changes", "No changes detected"),
            "current_values": result.get("current_values", {})
        }
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Attempted to parse: {content[:500]}")
        return {
            "summary": content,
            "key_changes": "Unable to extract changes",
            "current_values": {}
        }
    except Exception as e:
        print(f"Error parsing summarizer response: {e}")
        print(f"Raw response type: {type(response)}")
        return {
            "summary": str(response),
            "key_changes": "Unable to extract changes",
            "current_values": {}
        }
from langchain.agents import initialize_agent, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.search_and_location import get_user_location, get_user_summaries
import os
import json
from dotenv import load_dotenv
from config.settings import IPGEOLOCATION_API_KEY, GOOGLE_API_KEY, LLM_MODEL

load_dotenv()

def get_location_tool(_):
    """Wrapper for LangChain Tool interface (no input needed)."""
    return get_user_location(IPGEOLOCATION_API_KEY)

def create_location_search_agent():
    """
    Creates a location and search term agent with user location and summary retrieval tools
    
    Returns:
        LangChain agent
    """
    tools = [
        Tool(
            name="GetUserLocation",
            func=get_location_tool,
            description="Fetches the user's city, state, and country using their IP address. No input needed."
        ),
        Tool(
            name="GetUserSummaries",
            func=get_user_summaries,
            description="Fetches the user's most recent report summary from ChromaDB. Input: user_id (string)."
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

def run_search_term_and_location(user_id: str) -> dict:
    """
    Runs the location and search agent to find appropriate doctor specialization and location
    
    Args:
        user_id: Patient/User identifier
        summary: Optional medical summary (if not provided, will fetch from ChromaDB)
        
    Returns:
        Dictionary with 'doctor_type' and 'location' information
    """
    agent = create_location_search_agent()
    
    prompt = f"""
    You are a medical search assistant.

    Given the patient's medical information, do the following:
    1. Use the GetUserSummaries tool to fetch the most recent report summary for user_id: {user_id}
    2. Identify the most appropriate and specific doctor subspecialization (e.g., instead of Cardiologist specify Electrophysiologist, instead of Gastroenterologist specify Hepatologist, etc.)
       based on the symptoms, diagnosis, or treatment described in the summary, not just the broad category.
    3. Use the GetUserLocation tool to fetch the current user location.
    4. Return BOTH the doctor type and location as a structured JSON in the format:

    {{
      "doctor_type": "<doctor subspecialization>",
      "location": {{
        "city": "<city>",
        "state": "<state>",
        "country": "<country>"
      }}
    }}

    IMPORTANT: Your final answer MUST be valid JSON only, without any additional text or explanation.
    """
    
    response = agent.invoke({"input": prompt})
    
    output = response.get("output", "")
    
    try:
        if isinstance(output, str):
            if '```json' in output:
                output = output.split('```json')[1].split('```')[0].strip()
            elif '```' in output:
                parts = output.split('```')
                for part in parts:
                    if '{' in part and '}' in part:
                        output = part.strip()
                        break
            
            result = json.loads(output)
        else:
            result = output
            
        return {
            "doctor_type": result.get("doctor_type", "Unknown"),
            "location": result.get("location", {
                "city": "Unknown",
                "state": "Unknown",
                "country": "Unknown"
            })
        }
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing agent response: {e}")
        print(f"Raw output: {output}")
        return {
            "doctor_type": "Unable to determine",
            "location": {
                "city": "Unknown",
                "state": "Unknown",
                "country": "Unknown"
            },
            "raw_output": output
        }

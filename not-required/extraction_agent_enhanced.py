"""
Enhanced Extraction Agent with Self-Correction and Validation
FIXED VERSION - Better output parsing and error handling
"""

from langchain.agents import initialize_agent, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.extraction_tools import get_content, save_findings
from config.settings import GOOGLE_API_KEY, LLM_MODEL
from agents.critic_agent.critic import CriticAgent, format_critique_report
import json
import re


def create_enhanced_extraction_agent():
    """
    Creates an enhanced extraction agent with validation capabilities
    """
    tools = [
        Tool(
            name="getContent",
            func=get_content,
            description="Fetch and return all report page contents as a string. Input: Metadata"
        ),
        Tool(
            name="saveFindings",
            func=save_findings,
            description="Save extracted findings and metadata. Input must be a dict with keys 'findings', 'values', and 'metadata'."
        )
    ]
    
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.1  # Low temperature for accuracy
    )
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent


def extract_findings_from_text(report_text: str) -> dict:
    """
    Fallback: Use LLM directly to extract findings when agent parsing fails
    
    Args:
        report_text: The report text content
        
    Returns:
        Dictionary with findings and values
    """
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.1
    )
    
    prompt = f"""
Extract medical information from the following report text.

Report Text:
{report_text}

CRITICAL RULES:
1. Extract ONLY information explicitly stated in the text
2. DO NOT infer or add information
3. Extract ALL lab values with exact numbers and units
4. Extract ALL clinical findings and observations

Return ONLY a valid JSON object in this EXACT format (no markdown, no explanation):
{{
  "findings": ["finding 1", "finding 2", "finding 3"],
  "values": {{"lab_name": "value with unit", "lab_name_2": "value with unit"}}
}}

JSON Response:
"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Clean the response
        content = content.strip()
        
        # Remove markdown code blocks if present
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        # Extract JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        result = json.loads(content)
        
        return {
            "findings": result.get("findings", []),
            "values": result.get("values", {})
        }
        
    except Exception as e:
        print(f"Fallback extraction error: {e}")
        return {"findings": [], "values": {}}


def run_extraction_with_retry(metadata: dict, max_retries: int = 3) -> dict:
    """
    Runs extraction with critic feedback loop and retry mechanism
    
    Args:
        metadata: Report metadata containing report_id
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with 'findings', 'values', and 'critique'
    """
    critic = CriticAgent()
    
    # Get report text for validation
    from tools.extraction_tools import get_content
    report_text = get_content(metadata)
    
    ocr_confidence = metadata.get("confidence", 1.0)
    
    attempt = 0
    best_result = None
    best_critique = None
    
    while attempt < max_retries:
        attempt += 1
        print(f"\n🔄 EXTRACTION ATTEMPT {attempt}/{max_retries}")
        
        try:
            # Use direct LLM extraction instead of agent
            # This is more reliable for structured output
            result = extract_findings_from_text(report_text)
            
            findings = result.get("findings", [])
            values = result.get("values", {})
            
            # Ensure findings and values are valid
            if not isinstance(findings, list):
                findings = []
            if not isinstance(values, dict):
                values = {}
            
            print(f"Extracted {len(findings)} findings and {len(values)} values")
            
            # Save findings if we have any
            if findings or values:
                try:
                    save_findings({
                        "findings": findings,
                        "values": values,
                        "metadata": metadata
                    })
                except Exception as e:
                    print(f"Warning: Could not save findings: {e}")
            
            # Run critic review
            critique = critic.review_extraction(
                findings=findings,
                values=values,
                report_text=report_text,
                ocr_confidence=ocr_confidence
            )
            
            print(format_critique_report(critique))
            
            # If passed, return immediately
            if critique.get("passed", False):
                print(f"✅ Extraction passed quality check on attempt {attempt}")
                return {
                    "findings": findings,
                    "values": values,
                    "critique": critique,
                    "attempts": attempt,
                    "success": True
                }
            
            # Store best result so far
            current_issues = len(critique.get("issues", []))
            best_issues = len(best_critique.get("issues", [])) if best_critique else float('inf')
            
            if current_issues < best_issues:
                best_result = {"findings": findings, "values": values}
                best_critique = critique
            
        except Exception as e:
            print(f"❌ Error in extraction attempt {attempt}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # If all retries exhausted, return best result with warnings
    print(f"⚠️ Max retries reached. Returning best result with warnings.")
    
    if best_result:
        return {
            "findings": best_result.get("findings", []),
            "values": best_result.get("values", {}),
            "critique": best_critique if best_critique else {"passed": False, "issues": []},
            "attempts": max_retries,
            "success": False,
            "warning": "Extraction completed with quality issues"
        }
    
    # If no valid result at all
    return {
        "findings": [],
        "values": {},
        "critique": {"passed": False, "issues": [{"message": "Extraction failed completely"}]},
        "attempts": max_retries,
        "success": False,
        "error": "Failed to extract any valid data"
    }


def run_extraction(metadata: dict) -> dict:
    """
    Main entry point for extraction with validation
    
    Args:
        metadata: Report metadata
        
    Returns:
        Extraction results with validation
    """
    return run_extraction_with_retry(metadata, max_retries=3)
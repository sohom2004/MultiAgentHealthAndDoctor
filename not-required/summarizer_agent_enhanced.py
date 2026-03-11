"""
Enhanced Summarizer Agent with Evidence-Based Output
Ensures all summary statements are backed by extracted data
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from tools.summarizer_tools import get_all_findings, store_summaries
from config.settings import GOOGLE_API_KEY, LLM_MODEL
from config.medical_validation import validate_all_findings
import json
import re


def clean_json_response(content: str) -> str:
    """
    Cleans JSON response by removing markdown code blocks and extra text
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


def create_evidence_based_summarizer():
    """
    Creates a summarizer that requires evidence for all statements
    """
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )
    
    prompt = PromptTemplate(
        input_variables=["latest", "history", "validation"],
        template="""
You are a medical summarization agent. You MUST only state facts that are directly supported by the provided data.

Latest findings and values:
{latest}

Validation results (flagged abnormal values):
{validation}

Past reports (for context):
{history}

CRITICAL RULES:
1. Every statement MUST reference specific lab values or findings from the data above
2. DO NOT make general medical statements not supported by the data
3. DO NOT diagnose conditions - only describe findings
4. Highlight all abnormal values with their severity
5. Compare with previous reports when available

Return ONLY valid JSON with this EXACT structure:
{{
  "summary": "Evidence-based summary with specific references",
  "key_changes": "Comparison with previous data (or 'First report' if none)",
  "current_values": {{"parameter": "value unit"}},
  "abnormal_values": [
    {{
      "lab": "test name",
      "value": "current value",
      "reference": "normal range",
      "severity": "severity level",
      "evidence": "exact data point from findings"
    }}
  ],
  "evidence_map": {{
    "statement": "supporting data from findings/values"
  }}
}}

IMPORTANT: 
- In the summary, use phrases like "Lab results show X" or "Patient reports Y" (cite the evidence)
- Flag ALL abnormal values with severity
- If comparing with history, cite specific previous values
"""
    )
    
    summarizer_chain = prompt | llm
    return summarizer_chain


def run_evidence_based_summarization(patient_id: str) -> dict:
    """
    Runs evidence-based summarization with validation
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Dictionary with evidence-backed summary
    """
    reports = get_all_findings(patient_id)
    
    if not reports:
        return {
            "summary": "No stored findings for this patient.",
            "key_changes": "N/A",
            "current_values": {},
            "abnormal_values": [],
            "evidence_map": {},
            "confidence": "low",
            "warning": "No data available"
        }
    
    latest = reports[-1]
    history = reports[:-1] if len(reports) > 1 else []
    
    # Validate current values
    current_values = latest.get("values", {})
    validation_result = validate_all_findings(current_values)
    
    # Format validation for prompt
    validation_summary = {
        "abnormal_count": len(validation_result["flagged_values"]),
        "critical_count": len(validation_result["critical_values"]),
        "flagged_values": validation_result["flagged_values"],
        "validation_details": validation_result["validation_results"]
    }
    
    summarizer = create_evidence_based_summarizer()
    
    try:
        response = summarizer.invoke({
            "latest": json.dumps(latest, indent=2),
            "history": json.dumps(history, indent=2),
            "validation": json.dumps(validation_summary, indent=2)
        })
        
        content = response.content if hasattr(response, 'content') else str(response)
        content = clean_json_response(content)
        result = json.loads(content)
        
        # Verify evidence backing
        evidence_check = verify_evidence_backing(result, latest)
        
        # Format final summary with validation
        summary_text = format_evidence_based_summary(result, validation_result, evidence_check)
        
        # Store the summary
        store_summaries(summary_text, patient_id)
        
        return {
            "summary": result.get("summary", "No summary available"),
            "key_changes": result.get("key_changes", "No changes detected"),
            "current_values": result.get("current_values", {}),
            "abnormal_values": result.get("abnormal_values", []),
            "evidence_map": result.get("evidence_map", {}),
            "validation_results": validation_result,
            "evidence_check": evidence_check,
            "confidence": "high" if evidence_check["verified"] else "low"
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        return {
            "summary": "Error generating summary",
            "key_changes": "Unable to extract changes",
            "current_values": {},
            "abnormal_values": [],
            "evidence_map": {},
            "confidence": "low",
            "error": str(e)
        }


def verify_evidence_backing(summary_result: dict, latest_data: dict) -> dict:
    """
    Verify that all statements in summary are backed by actual data
    
    Args:
        summary_result: Generated summary
        latest_data: Source data
        
    Returns:
        Verification results
    """
    summary_text = summary_result.get("summary", "")
    findings = latest_data.get("findings", [])
    values = latest_data.get("values", {})
    
    # Extract claims from summary
    sentences = summary_text.split('.')
    
    unverified_claims = []
    verified_claims = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Check if sentence references data
        found_support = False
        
        # Check against findings
        for finding in findings:
            if any(word.lower() in sentence.lower() for word in finding.split() if len(word) > 3):
                found_support = True
                verified_claims.append({
                    "claim": sentence,
                    "evidence": finding,
                    "type": "finding"
                })
                break
        
        # Check against values
        if not found_support:
            for lab_name, value in values.items():
                if lab_name.lower() in sentence.lower() or str(value).lower() in sentence.lower():
                    found_support = True
                    verified_claims.append({
                        "claim": sentence,
                        "evidence": f"{lab_name}: {value}",
                        "type": "value"
                    })
                    break
        
        if not found_support and len(sentence) > 10:
            unverified_claims.append(sentence)
    
    verification_rate = len(verified_claims) / (len(verified_claims) + len(unverified_claims)) if (len(verified_claims) + len(unverified_claims)) > 0 else 1.0
    
    return {
        "verified": verification_rate > 0.8,
        "verification_rate": verification_rate,
        "verified_claims": len(verified_claims),
        "unverified_claims": len(unverified_claims),
        "unsupported_statements": unverified_claims
    }


def format_evidence_based_summary(result: dict, validation: dict, evidence_check: dict) -> str:
    """
    Format the evidence-based summary with validation markers
    """
    output = "EVIDENCE-BASED MEDICAL SUMMARY\n"
    output += "=" * 70 + "\n\n"
    
    # Confidence indicator
    confidence = "HIGH ✅" if evidence_check["verified"] else "LOW ⚠️"
    output += f"Confidence Level: {confidence}\n"
    output += f"Evidence Verification: {evidence_check['verification_rate']:.0%}\n\n"
    
    # Main summary
    output += "CLINICAL SUMMARY:\n"
    output += result.get("summary", "No summary available") + "\n\n"
    
    # Abnormal values section
    if result.get("abnormal_values"):
        output += "ABNORMAL VALUES DETECTED:\n"
        output += "-" * 70 + "\n"
        for abnormal in result["abnormal_values"]:
            output += f"  • {abnormal['lab']}: {abnormal['value']}\n"
            output += f"    Reference Range: {abnormal.get('reference', 'N/A')}\n"
            output += f"    Severity: {abnormal['severity']}\n"
            output += f"    Evidence: {abnormal.get('evidence', 'From lab results')}\n\n"
    
    # Current values
    output += "CURRENT VALUES:\n"
    output += "-" * 70 + "\n"
    for param, value in result.get("current_values", {}).items():
        # Check if flagged
        flagged = any(
            v["lab"] == param
            for v in result.get("abnormal_values", [])
        )
        flag_marker = " ⚠️" if flagged else ""
        output += f"  {param}: {value}{flag_marker}\n"
    output += "\n"
    
    # Key changes
    output += "KEY CHANGES FROM PREVIOUS REPORTS:\n"
    output += "-" * 70 + "\n"
    output += result.get("key_changes", "No changes detected") + "\n\n"
    
    # Evidence verification notice
    if not evidence_check["verified"]:
        output += "⚠️ WARNING: Some statements may lack sufficient evidence backing\n"
        output += f"Unverified claims: {evidence_check['unverified_claims']}\n\n"
    
    return output


def run_summarization(patient_id: str) -> dict:
    """
    Main entry point for evidence-based summarization
    """
    return run_evidence_based_summarization(patient_id)
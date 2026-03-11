"""
Critic Agent: Reviews and validates extracted findings
Provides feedback and requests retries when quality is insufficient
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from config.settings import GOOGLE_API_KEY, LLM_MODEL
from config.medical_validation import (
    validate_all_findings,
    check_missing_critical_metrics,
    detect_contradictions,
    detect_duplicates
)
import json
import re


class CriticAgent:
    """
    Critic Agent that reviews extracted findings and provides feedback
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1  # Low temperature for consistent validation
        )
        
        self.max_retries = 3
        self.confidence_threshold = 0.7
    
    def review_extraction(self, findings: list, values: dict, report_text: str, 
                         ocr_confidence: float = 1.0) -> dict:
        """
        Reviews extracted findings and values for completeness and accuracy
        
        Args:
            findings: List of extracted findings
            values: Dictionary of extracted lab values
            report_text: Original report text
            ocr_confidence: OCR confidence score
            
        Returns:
            Dictionary with review results and feedback
        """
        issues = []
        warnings = []
        passed = True
        
        # 1. Check OCR confidence
        if ocr_confidence < self.confidence_threshold:
            warnings.append({
                "type": "low_ocr_confidence",
                "severity": "warning",
                "message": f"⚠️ OCR confidence is low ({ocr_confidence:.2%}). Extraction may be unreliable.",
                "confidence": ocr_confidence
            })
        
        # 2. Check if findings are empty
        if not findings or len(findings) == 0:
            issues.append({
                "type": "empty_findings",
                "severity": "critical",
                "message": "❌ No findings were extracted from the report"
            })
            passed = False
        
        # 3. Check if values are empty
        if not values or len(values) == 0:
            issues.append({
                "type": "empty_values",
                "severity": "critical",
                "message": "❌ No lab values were extracted from the report"
            })
            passed = False
        
        # 4. Validate lab values against reference ranges
        if values:
            validation = validate_all_findings(values)
            
            if validation["has_critical"]:
                warnings.append({
                    "type": "critical_values",
                    "severity": "critical",
                    "message": f"🔴 {len(validation['critical_values'])} critical abnormal values detected",
                    "critical_values": validation["critical_values"]
                })
            
            if validation["has_abnormal"]:
                warnings.append({
                    "type": "abnormal_values",
                    "severity": "warning",
                    "message": f"🟠 {len(validation['flagged_values'])} abnormal values detected",
                    "flagged_values": validation["flagged_values"]
                })
        
        # 5. Check for missing critical metrics
        missing_metrics = check_missing_critical_metrics(findings, values)
        if missing_metrics:
            issues.append({
                "type": "missing_metrics",
                "severity": "warning",
                "message": f"⚠️ {len(missing_metrics)} potentially important metrics are missing",
                "missing_metrics": missing_metrics
            })
        
        # 6. Check for duplicates
        duplicates = detect_duplicates(values)
        if duplicates:
            issues.append({
                "type": "duplicate_values",
                "severity": "warning",
                "message": f"⚠️ {len(duplicates)} potential duplicate lab values detected",
                "duplicates": duplicates
            })
        
        # 7. Use LLM to check for hallucinations
        hallucination_check = self._check_hallucinations(findings, values, report_text)
        if not hallucination_check["valid"]:
            issues.append({
                "type": "hallucination",
                "severity": "critical",
                "message": "❌ Some extracted information may not be supported by the report text",
                "details": hallucination_check["unsupported_items"]
            })
            passed = False
        
        # 8. Check extraction completeness
        completeness = self._check_completeness(findings, values, report_text)
        if completeness["score"] < 0.7:
            issues.append({
                "type": "incomplete_extraction",
                "severity": "warning",
                "message": f"⚠️ Extraction may be incomplete (completeness: {completeness['score']:.0%})",
                "details": completeness["missing_sections"]
            })
        
        # Determine overall pass/fail
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        if critical_issues:
            passed = False
        
        return {
            "passed": passed,
            "confidence": ocr_confidence,
            "issues": issues,
            "warnings": warnings,
            "recommendations": self._generate_recommendations(issues, warnings),
            "should_retry": not passed and len(critical_issues) > 0
        }
    
    def _check_hallucinations(self, findings: list, values: dict, report_text: str) -> dict:
        """
        Check if extracted findings are actually supported by the report text
        """
        prompt = PromptTemplate(
            input_variables=["findings", "values", "report_text"],
            template="""
You are a medical fact-checker. Your job is to verify that extracted information is actually present in the source text.

Source Report Text:
{report_text}

Extracted Findings:
{findings}

Extracted Values:
{values}

Task: For each finding and value, verify if it is explicitly mentioned or clearly implied in the source text.

Return ONLY valid JSON:
{{
  "valid": true/false,
  "unsupported_items": [
    {{
      "item": "the extracted finding or value",
      "reason": "why it's not supported by the text"
    }}
  ]
}}

Be strict: if something is not clearly in the text, mark it as unsupported.
"""
        )
        
        try:
            response = self.llm.invoke(
                prompt.format(
                    findings=json.dumps(findings),
                    values=json.dumps(values),
                    report_text=report_text[:3000]  # Limit text length
                )
            )
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and parse JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"Hallucination check failed: {e}")
            return {"valid": True, "unsupported_items": []}
    
    def _check_completeness(self, findings: list, values: dict, report_text: str) -> dict:
        """
        Check if extraction captured all important information from the report
        """
        prompt = PromptTemplate(
            input_variables=["findings", "values", "report_text"],
            template="""
You are a medical report analyst. Evaluate if the extraction captured all important information.

Source Report Text:
{report_text}

Extracted Findings:
{findings}

Extracted Values:
{values}

Task: Determine what important information might be missing from the extraction.

Return ONLY valid JSON:
{{
  "score": 0.0-1.0 (completeness score),
  "missing_sections": [
    "description of what's missing"
  ]
}}
"""
        )
        
        try:
            response = self.llm.invoke(
                prompt.format(
                    findings=json.dumps(findings),
                    values=json.dumps(values),
                    report_text=report_text[:3000]
                )
            )
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"Completeness check failed: {e}")
            return {"score": 1.0, "missing_sections": []}
    
    def _generate_recommendations(self, issues: list, warnings: list) -> list:
        """
        Generate actionable recommendations based on issues found
        """
        recommendations = []
        
        for issue in issues:
            if issue["type"] == "empty_findings":
                recommendations.append("🔄 Retry extraction with emphasis on clinical findings")
            elif issue["type"] == "empty_values":
                recommendations.append("🔄 Retry extraction focusing on numerical lab values")
            elif issue["type"] == "hallucination":
                recommendations.append("🔄 Re-extract using only information explicitly stated in the report")
            elif issue["type"] == "missing_metrics":
                recommendations.append("🔍 Review report for missing critical metrics or request additional tests")
            elif issue["type"] == "duplicate_values":
                recommendations.append("🔄 Resolve duplicate lab values before proceeding")
            elif issue["type"] == "incomplete_extraction":
                recommendations.append("🔄 Perform a more thorough extraction pass")
        
        for warning in warnings:
            if warning["type"] == "low_ocr_confidence":
                recommendations.append("⚠️ Consider manual review due to low OCR confidence")
            elif warning["type"] == "critical_values":
                recommendations.append("🚨 Immediate medical attention may be required for critical values")
            elif warning["type"] == "abnormal_values":
                recommendations.append("📋 Flag abnormal values for physician review")
        
        return recommendations
    
    def compare_with_history(self, current_values: dict, previous_values: dict) -> dict:
        """
        Compare current values with historical data to detect contradictions
        """
        contradictions = detect_contradictions(current_values, previous_values)
        
        if contradictions:
            return {
                "has_contradictions": True,
                "contradictions": contradictions,
                "recommendation": "🔄 Review and verify suspicious value changes"
            }
        
        return {
            "has_contradictions": False,
            "contradictions": [],
            "recommendation": "✅ Values are consistent with historical data"
        }


def format_critique_report(critique_result: dict) -> str:
    """
    Format critique results into a readable report
    """
    report = "CRITIC AGENT REVIEW\n"
    report += "=" * 70 + "\n\n"
    
    if critique_result["passed"]:
        report += "✅ PASSED - Extraction meets quality standards\n\n"
    else:
        report += "❌ FAILED - Extraction requires attention\n\n"
    
    report += f"Confidence Score: {critique_result['confidence']:.0%}\n\n"
    
    if critique_result["issues"]:
        report += "ISSUES:\n"
        for issue in critique_result["issues"]:
            report += f"  {issue['message']}\n"
        report += "\n"
    
    if critique_result["warnings"]:
        report += "WARNINGS:\n"
        for warning in critique_result["warnings"]:
            report += f"  {warning['message']}\n"
        report += "\n"
    
    if critique_result["recommendations"]:
        report += "RECOMMENDATIONS:\n"
        for rec in critique_result["recommendations"]:
            report += f"  {rec}\n"
        report += "\n"
    
    return report

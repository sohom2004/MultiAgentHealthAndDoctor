"""
Enhanced Agentic Graph State with Validation and Feedback
"""

from typing import TypedDict, Optional, Dict, Any, List
from typing_extensions import Annotated
import operator


class AgenticState(TypedDict):
    # Input
    input_type: str  # "pdf", "image", "audio", "text"
    file_path: Optional[str]
    text_input: Optional[str]
    patient_id: str
    
    # OCR/STT outputs
    extracted_text: Optional[str]
    confidence: Optional[float]
    
    # Document Save outputs
    report_metadata: Optional[Dict[str, Any]]
    
    # Extraction outputs with validation
    findings: Optional[List[str]]
    values: Optional[Dict[str, Any]]
    extraction_attempts: int
    extraction_critique: Optional[Dict[str, Any]]
    extraction_confidence: Optional[float]
    
    # Summarizer outputs with evidence
    summary: Optional[str]
    key_changes: Optional[str]
    current_values: Optional[Dict[str, Any]]
    abnormal_values: Optional[List[Dict[str, Any]]]
    evidence_map: Optional[Dict[str, str]]
    summary_confidence: Optional[str]
    
    # Validation results
    validation_results: Optional[Dict[str, Any]]
    missing_metrics: Optional[List[Dict[str, Any]]]
    contradictions: Optional[List[Dict[str, Any]]]
    duplicates: Optional[List[Dict[str, Any]]]
    
    # Doctor Search outputs with refinement
    doctor_type: Optional[str]
    location: Optional[Dict[str, str]]
    search_params: Optional[Dict[str, Any]]
    search_results: Optional[Dict[str, Any]]
    top_doctors: Optional[List[Dict[str, Any]]]
    total_results: Optional[int]
    search_refinement_needed: Optional[bool]
    raw_search_output: Optional[str]
    
    # Agent collaboration
    clinical_feedback_to_search: Optional[str]
    search_refinement_request: Optional[str]
    
    # Final response
    final_response: Optional[str]
    
    # Error handling and retry logic
    error: Optional[str]
    warnings: Optional[List[str]]
    should_retry: Optional[bool]
    retry_count: int
    max_retries: int
    
    # Routing with conditions
    next_step: Optional[str]
    validation_passed: Optional[bool]
    critic_approved: Optional[bool]
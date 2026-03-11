"""
Medical Validation Rules and Reference Ranges
Provides rule-based validation for lab values and clinical metrics
"""

# Standard lab reference ranges (adult values)
LAB_REFERENCE_RANGES = {
    # Complete Blood Count (CBC)
    "hemoglobin": {"min": 12.0, "max": 17.5, "unit": "g/dL", "male_min": 13.5, "female_min": 12.0},
    "hematocrit": {"min": 36.0, "max": 50.0, "unit": "%", "male_min": 40.0, "female_min": 36.0},
    "rbc": {"min": 4.2, "max": 6.1, "unit": "million/μL"},
    "wbc": {"min": 4.5, "max": 11.0, "unit": "thousand/μL"},
    "platelets": {"min": 150, "max": 400, "unit": "thousand/μL"},
    
    # Metabolic Panel
    "glucose": {"min": 70, "max": 100, "unit": "mg/dL", "fasting": True},
    "glucose_random": {"min": 70, "max": 140, "unit": "mg/dL"},
    "hba1c": {"min": 4.0, "max": 5.6, "unit": "%"},
    "creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dL"},
    "bun": {"min": 7, "max": 20, "unit": "mg/dL"},
    "sodium": {"min": 136, "max": 145, "unit": "mEq/L"},
    "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L"},
    "chloride": {"min": 96, "max": 106, "unit": "mEq/L"},
    "calcium": {"min": 8.5, "max": 10.5, "unit": "mg/dL"},
    
    # Lipid Panel
    "total_cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
    "ldl": {"min": 0, "max": 100, "unit": "mg/dL"},
    "hdl": {"min": 40, "max": 999, "unit": "mg/dL"},
    "triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"},
    
    # Liver Function
    "alt": {"min": 7, "max": 56, "unit": "U/L"},
    "ast": {"min": 10, "max": 40, "unit": "U/L"},
    "alkaline_phosphatase": {"min": 44, "max": 147, "unit": "U/L"},
    "bilirubin_total": {"min": 0.1, "max": 1.2, "unit": "mg/dL"},
    "albumin": {"min": 3.5, "max": 5.5, "unit": "g/dL"},
    
    # Thyroid
    "tsh": {"min": 0.4, "max": 4.0, "unit": "mIU/L"},
    "t3": {"min": 80, "max": 200, "unit": "ng/dL"},
    "t4": {"min": 4.5, "max": 12.0, "unit": "μg/dL"},
    
    # Cardiac
    "troponin": {"min": 0, "max": 0.04, "unit": "ng/mL"},
    "bnp": {"min": 0, "max": 100, "unit": "pg/mL"},
    "ck_mb": {"min": 0, "max": 25, "unit": "U/L"},
    
    # Vitals
    "systolic_bp": {"min": 90, "max": 120, "unit": "mmHg"},
    "diastolic_bp": {"min": 60, "max": 80, "unit": "mmHg"},
    "heart_rate": {"min": 60, "max": 100, "unit": "bpm"},
    "temperature": {"min": 97.0, "max": 99.0, "unit": "°F"},
    "spo2": {"min": 95, "max": 100, "unit": "%"},
}

# Severity levels for abnormal values
SEVERITY_LEVELS = {
    "critical_high": {"label": "🔴 Critical High", "priority": 5},
    "high": {"label": "🟠 High", "priority": 4},
    "borderline_high": {"label": "🟡 Borderline High", "priority": 3},
    "normal": {"label": "🟢 Normal", "priority": 1},
    "borderline_low": {"label": "🟡 Borderline Low", "priority": 3},
    "low": {"label": "🟠 Low", "priority": 4},
    "critical_low": {"label": "🔴 Critical Low", "priority": 5},
}


def normalize_lab_name(lab_name: str) -> str:
    """
    Normalize lab test names to match reference ranges
    
    Args:
        lab_name: Raw lab test name from extraction
        
    Returns:
        Normalized lab name
    """
    lab_name = lab_name.lower().strip()
    
    # Common variations mapping
    name_mapping = {
        "hgb": "hemoglobin",
        "hb": "hemoglobin",
        "hct": "hematocrit",
        "rbc count": "rbc",
        "wbc count": "wbc",
        "plt": "platelets",
        "fbs": "glucose",
        "blood sugar": "glucose",
        "blood glucose": "glucose",
        "a1c": "hba1c",
        "glycated hemoglobin": "hba1c",
        "chol": "total_cholesterol",
        "cholesterol": "total_cholesterol",
        "ldl cholesterol": "ldl",
        "hdl cholesterol": "hdl",
        "tg": "triglycerides",
        "sgpt": "alt",
        "sgot": "ast",
        "alp": "alkaline_phosphatase",
        "blood pressure": "bp",
        "pulse": "heart_rate",
        "oxygen saturation": "spo2",
    }
    
    for pattern, normalized in name_mapping.items():
        if pattern in lab_name:
            return normalized
    
    return lab_name


def extract_numeric_value(value_str: str) -> float:
    """
    Extract numeric value from string (handles units, ranges, etc.)
    
    Args:
        value_str: String containing numeric value
        
    Returns:
        Float value or None
    """
    import re
    
    if isinstance(value_str, (int, float)):
        return float(value_str)
    
    # Remove common units and extract number
    value_str = str(value_str).strip()
    
    # Handle ranges (take the first value)
    if '-' in value_str and value_str[0] != '-':
        value_str = value_str.split('-')[0].strip()
    
    # Extract first number found
    match = re.search(r'[-+]?\d*\.?\d+', value_str)
    if match:
        return float(match.group())
    
    return None


def validate_lab_value(lab_name: str, value: str, gender: str = None) -> dict:
    """
    Validate a lab value against reference ranges
    
    Args:
        lab_name: Name of the lab test
        value: Lab value (string or numeric)
        gender: Patient gender ('male' or 'female') if relevant
        
    Returns:
        Dictionary with validation results
    """
    normalized_name = normalize_lab_name(lab_name)
    numeric_value = extract_numeric_value(value)
    
    if numeric_value is None:
        return {
            "valid": False,
            "error": "Could not extract numeric value",
            "severity": None,
            "flag": None
        }
    
    if normalized_name not in LAB_REFERENCE_RANGES:
        return {
            "valid": True,
            "severity": "normal",
            "flag": None,
            "message": "No reference range available for this test"
        }
    
    ref_range = LAB_REFERENCE_RANGES[normalized_name]
    
    # Adjust for gender-specific ranges
    min_val = ref_range.get(f"{gender}_min", ref_range["min"])
    max_val = ref_range["max"]
    
    # Calculate deviation
    range_width = max_val - min_val
    deviation_percent = 0
    
    if numeric_value < min_val:
        deviation_percent = ((min_val - numeric_value) / range_width) * 100
        
        if deviation_percent > 50:
            severity = "critical_low"
        elif deviation_percent > 25:
            severity = "low"
        else:
            severity = "borderline_low"
            
    elif numeric_value > max_val:
        deviation_percent = ((numeric_value - max_val) / range_width) * 100
        
        if deviation_percent > 50:
            severity = "critical_high"
        elif deviation_percent > 25:
            severity = "high"
        else:
            severity = "borderline_high"
    else:
        severity = "normal"
    
    return {
        "valid": True,
        "lab_name": normalized_name,
        "value": numeric_value,
        "unit": ref_range.get("unit", ""),
        "reference_range": f"{min_val}-{max_val}",
        "severity": severity,
        "severity_label": SEVERITY_LEVELS[severity]["label"],
        "priority": SEVERITY_LEVELS[severity]["priority"],
        "deviation_percent": abs(deviation_percent),
        "flag": severity != "normal",
        "message": f"Value is {severity.replace('_', ' ')}"
    }


def validate_all_findings(values: dict, gender: str = None) -> dict:
    """
    Validate all lab values in findings
    
    Args:
        values: Dictionary of lab name -> value pairs
        gender: Patient gender
        
    Returns:
        Dictionary with validation results for all values
    """
    validation_results = {}
    flagged_values = []
    critical_values = []
    
    for lab_name, value in values.items():
        result = validate_lab_value(lab_name, value, gender)
        validation_results[lab_name] = result
        
        if result.get("flag"):
            flagged_values.append({
                "lab": lab_name,
                "value": value,
                "severity": result["severity"],
                "priority": result["priority"]
            })
            
            if "critical" in result["severity"]:
                critical_values.append({
                    "lab": lab_name,
                    "value": value,
                    "severity": result["severity"]
                })
    
    # Sort flagged values by priority
    flagged_values.sort(key=lambda x: x["priority"], reverse=True)
    
    return {
        "validation_results": validation_results,
        "flagged_values": flagged_values,
        "critical_values": critical_values,
        "has_abnormal": len(flagged_values) > 0,
        "has_critical": len(critical_values) > 0
    }


def detect_contradictions(current_values: dict, previous_values: dict) -> list:
    """
    Detect contradictory or impossible changes between reports
    
    Args:
        current_values: Current report values
        previous_values: Previous report values
        
    Returns:
        List of detected contradictions
    """
    contradictions = []
    
    for lab_name, current_val in current_values.items():
        if lab_name in previous_values:
            prev_val = extract_numeric_value(previous_values[lab_name])
            curr_val = extract_numeric_value(current_val)
            
            if prev_val and curr_val:
                # Detect impossible changes (>300% increase or decrease in short time)
                change_ratio = abs(curr_val - prev_val) / prev_val if prev_val != 0 else 0
                
                if change_ratio > 3.0:
                    contradictions.append({
                        "lab": lab_name,
                        "previous_value": prev_val,
                        "current_value": curr_val,
                        "change_ratio": change_ratio,
                        "message": f"Suspicious change: {prev_val} → {curr_val} ({change_ratio*100:.0f}% change)"
                    })
    
    return contradictions


def detect_duplicates(values: dict) -> list:
    """
    Detect duplicate lab values that might indicate extraction errors
    
    Args:
        values: Dictionary of lab values
        
    Returns:
        List of potential duplicates
    """
    duplicates = []
    seen_values = {}
    
    for lab_name, value in values.items():
        normalized_name = normalize_lab_name(lab_name)
        numeric_value = extract_numeric_value(value)
        
        if numeric_value:
            if normalized_name in seen_values:
                duplicates.append({
                    "lab_1": seen_values[normalized_name]["original_name"],
                    "lab_2": lab_name,
                    "normalized_name": normalized_name,
                    "value": numeric_value,
                    "message": f"Potential duplicate: {seen_values[normalized_name]['original_name']} and {lab_name}"
                })
            else:
                seen_values[normalized_name] = {
                    "original_name": lab_name,
                    "value": numeric_value
                }
    
    return duplicates


def check_missing_critical_metrics(findings: list, values: dict) -> list:
    """
    Check for missing critical clinical metrics based on findings
    
    Args:
        findings: List of clinical findings
        values: Dictionary of extracted values
        
    Returns:
        List of missing critical metrics
    """
    missing_metrics = []
    
    # Define critical metrics by condition/finding
    critical_metrics_map = {
        "diabetes": ["glucose", "hba1c"],
        "hypertension": ["systolic_bp", "diastolic_bp"],
        "heart": ["troponin", "bnp", "cholesterol"],
        "kidney": ["creatinine", "bun"],
        "liver": ["alt", "ast", "bilirubin"],
        "anemia": ["hemoglobin", "rbc", "hematocrit"],
        "thyroid": ["tsh", "t3", "t4"],
        "infection": ["wbc"],
    }
    
    # Check findings for relevant conditions
    findings_text = " ".join(findings).lower()
    
    for condition, required_metrics in critical_metrics_map.items():
        if condition in findings_text:
            for metric in required_metrics:
                # Check if metric is present in values
                metric_found = any(
                    normalize_lab_name(lab_name) == metric
                    for lab_name in values.keys()
                )
                
                if not metric_found:
                    missing_metrics.append({
                        "condition": condition,
                        "missing_metric": metric,
                        "message": f"Missing {metric} for {condition} evaluation"
                    })
    
    return missing_metrics

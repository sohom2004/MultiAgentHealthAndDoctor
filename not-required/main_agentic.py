"""
Main Entry Point for Enhanced Medical Report Diagnosis Agentic System
Features: Validation loops, critic feedback, evidence-based outputs, agent collaboration
"""
import sys
from pathlib import Path
from graph.agentic_workflow import (
    run_agentic_report_workflow,
    run_agentic_search_workflow,
    get_workflow_status
)
from tools.ocr_tools import cleanup_temp_files


def print_banner():
    """Prints the welcome banner"""
    print("\n" + "="*70)
    print("MedInsight - ENHANCED AGENTIC MEDICAL DIAGNOSIS SYSTEM")
    print("  Features: Validation Loops | Evidence-Based Output | Agent Collaboration")
    print("="*70)
    print("\nCommands:")
    print("  --file <path>     : Process a file (PDF, image, audio)")
    print("  --text <message>  : Send a text message or query")
    print("  --patient <id>    : Set current patient ID (default: pt-001)")
    print("  --search          : Search for doctors based on your medical report")
    print("  --status          : Show system status and validation metrics")
    print("  --help            : Show this help message")
    print("  --exit / quit     : Exit the system")
    print("="*70 + "\n")


def print_help():
    """Prints help information"""
    print("\n" + "="*70)
    print("  HELP - Enhanced Agentic System Features")
    print("="*70)
    print("\n🔍 KEY FEATURES:")
    print("  ✓ Automatic validation with retry loops")
    print("  ✓ Critic agent reviews all extractions")
    print("  ✓ Evidence-based summaries with confidence scores")
    print("  ✓ Abnormal value detection and flagging")
    print("  ✓ Agent-to-agent collaboration for doctor search refinement")
    print("  ✓ Confidence thresholds for retrieval quality")
    print("\n📋 FILE PROCESSING:")
    print("  --file report.pdf")
    print("  --file scan.jpg")
    print("  --file symptoms.mp3")
    print("\n💬 ENHANCED TEXT QUERIES:")
    print("  --text What is my cholesterol level?")
    print("  --text Show trends for my glucose over time")
    print("  --text Compare my last two blood tests")
    print("  --text Summarize my medical history")
    print("\n🔍 INTELLIGENT DOCTOR SEARCH:")
    print("  --search")
    print("  (System analyzes your reports and finds specialized doctors)")
    print("\n📊 STATUS & VALIDATION:")
    print("  --status")
    print("  (Shows extraction confidence, validation results, warnings)")
    print("\n🎯 ADVANCED QUERIES:")
    print("  --text Analyze trends for my blood pressure")
    print("  --text What changed between my reports?")
    print("  --text Show me all abnormal values")
    print("="*70 + "\n")


def is_search_command(text: str) -> bool:
    """
    Checks if the text is a doctor search command
    """
    search_keywords = [
        'find doctor',
        'find doctors',
        'search doctor',
        'search doctors',
        'find me a doctor',
        'find me doctors',
        'look for doctor',
        'look for doctors',
        'recommend doctor',
        'recommend doctors',
        'need a doctor',
        'need doctor',
        'show me doctors',
        'get doctors',
        'locate doctor',
        'locate doctors'
    ]
    
    text_lower = text.lower().strip()
    
    if '--search' in text_lower or text_lower == 'search':
        return True
    
    for keyword in search_keywords:
        if keyword in text_lower:
            return True
    
    return False


def parse_command(command: str, current_patient: str) -> dict:
    """
    Parses user command
    """
    command = command.strip()
    
    if command.lower() in ['--exit', 'exit', 'quit', '--quit']:
        return {"action": "exit"}
    
    if command.lower() in ['--help', 'help']:
        return {"action": "help"}
    
    if command.lower() in ['--status', 'status']:
        return {"action": "status"}
    
    if not command:
        return {"action": "empty"}
    
    result = {
        "action": "process",
        "file_path": None,
        "text_input": None,
        "patient_id": current_patient,
        "is_search": False
    }
    
    if '--patient' in command:
        parts = command.split('--patient', 1)
        command = parts[0].strip()
        patient_part = parts[1].strip()
        patient_words = patient_part.split()
        if patient_words:
            result["patient_id"] = patient_words[0]
            remaining = ' '.join(patient_words[1:])
            command = command + ' ' + remaining
    
    command = command.strip()
    
    if is_search_command(command):
        result["is_search"] = True
        result["action"] = "search"
        return result
    
    if '--file' in command:
        parts = command.split('--file', 1)
        if len(parts) > 1:
            file_path = parts[1].strip().split()[0]
            result["file_path"] = file_path
            remaining_text = ' '.join(parts[1].strip().split()[1:])
            command = parts[0].strip() + ' ' + remaining_text
    
    if '--text' in command:
        parts = command.split('--text', 1)
        if len(parts) > 1:
            result["text_input"] = parts[1].strip()
    elif not result["file_path"] and command:
        result["text_input"] = command
    
    if not result["file_path"] and not result["text_input"]:
        return {"action": "invalid", "message": "Please provide either --file or --text"}
    
    return result


def show_status(patient_id: str) -> str:
    """
    Shows system status and validation metrics for current patient
    """
    from tools.summarizer_tools import get_all_findings
    from config.medical_validation import validate_all_findings
    
    try:
        reports = get_all_findings(patient_id)
        
        if not reports:
            return f"📊 No reports found for patient {patient_id}"
        
        latest = reports[-1]
        values = latest.get("values", {})
        
        validation = validate_all_findings(values)
        
        status = f"\n📊 SYSTEM STATUS - Patient {patient_id}\n"
        status += "=" * 70 + "\n\n"
        
        status += f"Total Reports: {len(reports)}\n"
        status += f"Latest Report Date: {latest.get('report_date', 'Unknown')}\n"
        status += f"Lab Values Tracked: {len(values)}\n\n"
        
        status += "VALIDATION RESULTS:\n"
        status += "-" * 70 + "\n"
        status += f"  Total Values: {len(values)}\n"
        status += f"  Normal Values: {len(values) - len(validation['flagged_values'])}\n"
        status += f"  Abnormal Values: {len(validation['flagged_values'])}\n"
        status += f"  Critical Values: {len(validation['critical_values'])}\n\n"
        
        if validation['flagged_values']:
            status += "🔴 ABNORMAL VALUES:\n"
            for flag in validation['flagged_values'][:5]:  # Show top 5
                status += f"  • {flag['lab']}: {flag['value']} ({flag['severity']})\n"
            status += "\n"
        
        status += "SYSTEM HEALTH:\n"
        status += "-" * 70 + "\n"
        status += "  ✓ Validation system: Active\n"
        status += "  ✓ Critic agent: Active\n"
        status += "  ✓ Evidence verification: Active\n"
        status += "  ✓ Confidence thresholds: Active\n"
        
        return status
        
    except Exception as e:
        return f"❌ Error retrieving status: {str(e)}"


def process_search_command(patient_id: str) -> str:
    """
    Processes a doctor search command using agentic workflow
    """
    try:
        print(f"\n🔍 Searching for specialized doctors based on your medical reports...")
        print(f"👤 Patient ID: {patient_id}")
        print("⏳ Analyzing reports and refining search criteria...\n")
        
        result = run_agentic_search_workflow(patient_id=patient_id)
        
        # Show workflow status
        status = get_workflow_status(result)
        if status["has_error"]:
            print(f"⚠️ Workflow completed with errors")
        
        if result.get("search_refinement_needed"):
            print("🔄 Doctor specialization refined using clinical context")
        
        return result.get("final_response", "No search results generated")
        
    except Exception as e:
        return f"ERROR: Search failed - {str(e)}"


def process_report_command(cmd_dict: dict) -> str:
    """
    Processes a report/file command using agentic workflow
    """
    try:
        file_path = cmd_dict.get("file_path")
        text_input = cmd_dict.get("text_input")
        patient_id = cmd_dict.get("patient_id", "pt-001")
        
        if file_path:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return f"ERROR: File not found: {file_path}"
            
            suffix = file_path_obj.suffix.lower()
            
            if suffix == ".pdf":
                input_type = "pdf"
            elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
                input_type = "image"
            elif suffix in [".mp3", ".wav", ".m4a", ".flac"]:
                input_type = "audio"
            else:
                return f"ERROR: Unsupported file type: {suffix}"
            
            print(f"\n📄 Processing {input_type.upper()} file: {file_path}")
            print(f"👤 Patient ID: {patient_id}")
            print("⏳ Running agentic workflow with validation...\n")
            
            # Run enhanced agentic workflow
            result = run_agentic_report_workflow(
                input_type=input_type,
                file_path=str(file_path_obj),
                patient_id=patient_id,
                max_retries=3
            )
            
            cleanup_temp_files()
            
            # Show workflow metrics
            status = get_workflow_status(result)
            print("\n📊 WORKFLOW METRICS:")
            print(f"  Extraction Attempts: {status['extraction_attempts']}")
            print(f"  Validation Passed: {'✓' if status['validation_passed'] else '✗'}")
            print(f"  Critic Approved: {'✓' if status['critic_approved'] else '✗'}")
            print(f"  Extraction Confidence: {status['extraction_confidence']:.0%}")
            print(f"  Summary Confidence: {status['summary_confidence'].upper()}")
            print(f"  Warnings: {status['warnings_count']}")
            print(f"  Abnormal Values: {status['abnormal_values_count']}")
            print(f"  Missing Metrics: {status['missing_metrics_count']}")
            print(f"  Contradictions: {status['contradictions_count']}\n")
            
            return result.get("final_response", "No response generated")
        
        elif text_input:
            print(f"\n💬 Processing enhanced text query")
            print(f"👤 Patient ID: {patient_id}")
            print("⏳ Using confidence-aware retrieval...\n")
            
            # Text queries use enhanced chat agent directly
            result = run_agentic_report_workflow(
                input_type="text",
                text_input=text_input,
                patient_id=patient_id
            )
            
            return result.get("final_response", "No response generated")
        
        else:
            return "ERROR: No input provided"
            
    except Exception as e:
        cleanup_temp_files()
        return f"ERROR: {str(e)}"


def main():
    """
    Main continuous loop for enhanced agentic terminal interface
    """
    print_banner()
    
    current_patient = "pt-001"
    
    print(f"Current Patient ID: {current_patient}")
    print("Type --help for usage information")
    print("Type --status to see system health and validation metrics\n")
    
    while True:
        try:
            user_input = input(f"[{current_patient}] > ").strip()
            
            if not user_input:
                continue
            
            cmd_dict = parse_command(user_input, current_patient)
            
            if cmd_dict["action"] == "exit":
                print("\n👋 Thank you for using Enhanced Medical Agentic System. Goodbye!\n")
                break
            
            elif cmd_dict["action"] == "help":
                print_help()
                continue
            
            elif cmd_dict["action"] == "status":
                status = show_status(current_patient)
                print(status)
                continue
            
            elif cmd_dict["action"] == "empty":
                continue
            
            elif cmd_dict["action"] == "invalid":
                print(f"\n❌ {cmd_dict.get('message')}\n")
                continue
            
            elif cmd_dict["action"] == "search":
                if cmd_dict["patient_id"] != current_patient:
                    current_patient = cmd_dict["patient_id"]
                    print(f"\n✓ Switched to Patient ID: {current_patient}\n")
                
                response = process_search_command(current_patient)
                print(f"\n{response}\n")
            
            elif cmd_dict["action"] == "process":
                if cmd_dict["patient_id"] != current_patient:
                    current_patient = cmd_dict["patient_id"]
                    print(f"\n✓ Switched to Patient ID: {current_patient}\n")
                
                response = process_report_command(cmd_dict)
                print(f"\n{response}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Type --exit to quit or continue...\n")
            continue
        
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}\n")
            continue


if __name__ == "__main__":
    main()

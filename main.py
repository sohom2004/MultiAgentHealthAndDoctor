"""
Main entry point for the Medical Report Diagnosis Agentic System
Continuous terminal-based interface
"""
import sys
from pathlib import Path
from graph.workflow import run_report_workflow, run_search_workflow
from tools.ocr_tools import cleanup_temp_files


def print_banner():
    """Prints the welcome banner"""
    print("\n" + "="*70)
    print("  MEDICAL REPORT DIAGNOSIS AGENTIC SYSTEM")
    print("  Continuous Terminal Interface")
    print("="*70)
    print("\nCommands:")
    print("  --file <path>     : Process a file (PDF, image, audio)")
    print("  --text <message>  : Send a text message or query")
    print("  --patient <id>    : Set current patient ID (default: pt-001)")
    print("  --search          : Search for doctors based on your medical report")
    print("  --help            : Show this help message")
    print("  --exit / quit     : Exit the system")
    print("="*70 + "\n")


def print_help():
    """Prints help information"""
    print("\n" + "="*70)
    print("  HELP - How to Use")
    print("="*70)
    print("\nFile Processing:")
    print("  --file report.pdf")
    print("  --file scan.jpg")
    print("  --file symptoms.mp3")
    print("\nText Queries:")
    print("  --text What is my cholesterol level?")
    print("  --text Show me my medical history")
    print("  --text Blood pressure: 145/90, Glucose: 110 mg/dL")
    print("\nDoctor Search:")
    print("  --search")
    print("  find doctors")
    print("  search for doctors")
    print("  find me a doctor")
    print("\nChange Patient:")
    print("  --patient pt-002")
    print("\nCombined:")
    print("  --patient pt-001 --file report.pdf")
    print("\nExamples:")
    print("  > --text What were my last test results?")
    print("  > --file blood-test.pdf")
    print("  > --patient pt-002 --text Show history")
    print("  > --search")
    print("  > find me a cardiologist")
    print("="*70 + "\n")


def is_search_command(text: str) -> bool:
    """
    Checks if the text is a doctor search command
    
    Args:
        text: User input text
        
    Returns:
        True if it's a search command, False otherwise
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
    
    Args:
        command: User input string
        current_patient: Current patient ID
        
    Returns:
        Dictionary with parsed command details
    """
    command = command.strip()
    
    if command.lower() in ['--exit', 'exit', 'quit', '--quit']:
        return {"action": "exit"}
    
    if command.lower() in ['--help', 'help']:
        return {"action": "help"}
    
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


def process_search_command(patient_id: str) -> str:
    """
    Processes a doctor search command
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Response string with doctor search results
    """
    try:
        print(f"\n🔍 Searching for doctors based on your medical report...")
        print(f"👤 Patient ID: {patient_id}")
        print("⏳ Please wait...\n")
        
        result = run_search_workflow(patient_id=patient_id)
        
        return result.get("final_response", "No search results generated")
        
    except Exception as e:
        return f"ERROR: Search failed - {str(e)}"


def process_report_command(cmd_dict: dict) -> str:
    """
    Processes a report/file command
    
    Args:
        cmd_dict: Parsed command dictionary
        
    Returns:
        Response string
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
            print("⏳ Please wait...\n")
            
            result = run_report_workflow(
                input_type=input_type,
                file_path=str(file_path_obj),
                patient_id=patient_id
            )
            
            cleanup_temp_files()
            
            return result.get("final_response", "No response generated")
        
        elif text_input:
            print(f"\n💬 Processing text query")
            print(f"👤 Patient ID: {patient_id}")
            print("⏳ Please wait...\n")
            
            result = run_report_workflow(
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
    Main continuous loop for terminal interface
    """
    print_banner()
    
    current_patient = "pt-001"
    
    print(f"Current Patient ID: {current_patient}")
    print("Type --help for usage information\n")
    
    while True:
        try:
            user_input = input(f"[{current_patient}] > ").strip()
            
            if not user_input:
                continue
            
            cmd_dict = parse_command(user_input, current_patient)
            
            if cmd_dict["action"] == "exit":
                print("\n👋 Thank you for using Medical Agentic System. Goodbye!\n")
                break
            
            elif cmd_dict["action"] == "help":
                print_help()
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
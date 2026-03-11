"""
Streamlit UI for Medical Report Diagnosis Agentic System
"""
import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Import your existing modules
from graph.workflow import run_report_workflow, run_search_workflow
from tools.ocr_tools import cleanup_temp_files

# Page configuration
st.set_page_config(
    page_title="MedInsight",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: 600;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'patient_id' not in st.session_state:
    st.session_state.patient_id = "pt-001"
if 'history' not in st.session_state:
    st.session_state.history = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

def add_to_history(action, details, response):
    """Add an interaction to the history"""
    st.session_state.history.append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'patient_id': st.session_state.patient_id,
        'action': action,
        'details': details,
        'response': response
    })

def process_file(file, file_type, patient_id):
    """Process uploaded file"""
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"temp_{file.name}")
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())
        
        # Run workflow
        result = run_report_workflow(
            input_type=file_type,
            file_path=str(temp_path),
            patient_id=patient_id
        )
        
        # Cleanup
        cleanup_temp_files()
        if temp_path.exists():
            temp_path.unlink()
        
        return result.get("final_response", "No response generated")
    
    except Exception as e:
        cleanup_temp_files()
        return f"ERROR: {str(e)}"

def process_text(text_input, patient_id):
    """Process text query"""
    try:
        result = run_report_workflow(
            input_type="text",
            text_input=text_input,
            patient_id=patient_id
        )
        return result.get("final_response", "No response generated")
    
    except Exception as e:
        return f"ERROR: {str(e)}"

def process_search(patient_id):
    """Process doctor search"""
    try:
        result = run_search_workflow(patient_id=patient_id)
        return result.get("final_response", "No search results generated")
    
    except Exception as e:
        return f"ERROR: Search failed - {str(e)}"

# Header
st.markdown('<div class="main-header">🏥 Medical Report Diagnosis System</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Patient ID selector
    st.subheader("Patient Information")
    new_patient_id = st.text_input(
        "Patient ID",
        value=st.session_state.patient_id,
        help="Enter or modify patient ID"
    )
    
    if new_patient_id != st.session_state.patient_id:
        st.session_state.patient_id = new_patient_id
        st.success(f"✓ Switched to Patient: {new_patient_id}")
    
    st.divider()
    
    # Quick actions
    st.subheader("Quick Actions")
    
    if st.button("🔍 Search for Doctors", use_container_width=True):
        st.session_state.quick_action = "search"
    
    if st.button("📜 View History", use_container_width=True):
        st.session_state.quick_action = "history"
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.success("History cleared!")
    
    st.divider()
    
    # Information
    st.subheader("ℹ️ About")
    st.info("""
    This system analyzes medical reports and provides:
    - Medical report processing
    - Text-based queries
    - Audio transcription
    - Doctor recommendations
    - Patient history tracking
    """)

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📄 File Upload", "💬 Text Query", "🔍 Doctor Search", "📜 History"])

# Tab 1: File Upload
with tab1:
    st.header("Upload Medical Report")
    st.write("Upload a PDF, image, or audio file for analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "png", "jpg", "jpeg", "bmp", "tiff", "mp3", "wav", "m4a", "flac"],
            help="Supported formats: PDF, Images (PNG, JPG, etc.), Audio (MP3, WAV, etc.)"
        )
    
    with col2:
        st.info(f"**Current Patient:** {st.session_state.patient_id}")
    
    if uploaded_file is not None:
        # Display file info
        st.write(f"**Filename:** {uploaded_file.name}")
        st.write(f"**File size:** {uploaded_file.size / 1024:.2f} KB")
        
        # Determine file type
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix == ".pdf":
            file_type = "pdf"
            icon = "📄"
        elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            file_type = "image"
            icon = "🖼️"
            # Show image preview
            st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        elif suffix in [".mp3", ".wav", ".m4a", ".flac"]:
            file_type = "audio"
            icon = "🎵"
            st.audio(uploaded_file)
        else:
            st.error(f"Unsupported file type: {suffix}")
            file_type = None
        
        if file_type:
            if st.button(f"{icon} Process File", key="process_file_btn", use_container_width=True):
                with st.spinner(f"Processing {file_type.upper()} file... Please wait..."):
                    response = process_file(uploaded_file, file_type, st.session_state.patient_id)
                    
                    if response.startswith("ERROR"):
                        st.error(response)
                    else:
                        st.success("✓ File processed successfully!")
                        st.markdown("### Analysis Results")
                        st.write(response)
                        
                        # Add to history
                        add_to_history(
                            f"File Upload ({file_type})",
                            uploaded_file.name,
                            response
                        )

# Tab 2: Text Query
with tab2:
    st.header("Text-Based Query")
    st.write("Enter medical data or ask questions about your medical history")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.info(f"**Current Patient:** {st.session_state.patient_id}")
    
    # Example queries
    with st.expander("📝 Example Queries"):
        st.write("""
        - What is my cholesterol level?
        - Show me my medical history
        - Blood pressure: 145/90, Glucose: 110 mg/dL
        - What were my last test results?
        - Summarize my recent visits
        """)
    
    text_input = st.text_area(
        "Enter your query or medical data:",
        height=150,
        placeholder="Type your question or enter medical readings here..."
    )
    
    if st.button("💬 Submit Query", key="submit_text_btn", use_container_width=True):
        if text_input.strip():
            with st.spinner("Processing your query... Please wait..."):
                response = process_text(text_input, st.session_state.patient_id)
                
                if response.startswith("ERROR"):
                    st.error(response)
                else:
                    st.success("✓ Query processed successfully!")
                    st.markdown("### Response")
                    st.write(response)
                    
                    # Add to history
                    add_to_history(
                        "Text Query",
                        text_input[:100] + "..." if len(text_input) > 100 else text_input,
                        response
                    )
        else:
            st.warning("Please enter a query before submitting.")

# Tab 3: Doctor Search
with tab3:
    st.header("Find Doctors")
    st.write("Search for healthcare providers based on your medical report")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.info(f"**Current Patient:** {st.session_state.patient_id}")
    
    st.markdown("""
    This feature analyzes your medical history and recommends appropriate healthcare providers:
    - Specialists based on your conditions
    - Nearby healthcare facilities
    - Ratings and reviews
    """)
    
    if st.button("🔍 Search for Doctors", key="search_doctors_btn", use_container_width=True):
        with st.spinner("Searching for doctors based on your medical profile... Please wait..."):
            response = process_search(st.session_state.patient_id)
            
            if response.startswith("ERROR"):
                st.error(response)
            else:
                st.success("✓ Search completed!")
                st.markdown("### Recommended Doctors")
                st.write(response)
                
                # Add to history
                add_to_history(
                    "Doctor Search",
                    "Search for healthcare providers",
                    response
                )

# Tab 4: History
with tab4:
    st.header("Interaction History")
    
    if st.session_state.history:
        st.write(f"**Total interactions:** {len(st.session_state.history)}")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            filter_patient = st.selectbox(
                "Filter by Patient ID",
                ["All"] + list(set([h['patient_id'] for h in st.session_state.history]))
            )
        
        with col2:
            filter_action = st.selectbox(
                "Filter by Action Type",
                ["All"] + list(set([h['action'] for h in st.session_state.history]))
            )
        
        # Display history
        filtered_history = st.session_state.history
        if filter_patient != "All":
            filtered_history = [h for h in filtered_history if h['patient_id'] == filter_patient]
        if filter_action != "All":
            filtered_history = [h for h in filtered_history if h['action'] == filter_action]
        
        st.divider()
        
        for idx, item in enumerate(reversed(filtered_history)):
            with st.expander(f"🕐 {item['timestamp']} - {item['action']} ({item['patient_id']})"):
                st.markdown(f"**Patient ID:** {item['patient_id']}")
                st.markdown(f"**Action:** {item['action']}")
                st.markdown(f"**Details:** {item['details']}")
                st.markdown("**Response:**")
                st.write(item['response'])
    else:
        st.info("No interaction history yet. Start by uploading a file or submitting a query!")

# Handle quick actions from sidebar
if hasattr(st.session_state, 'quick_action'):
    if st.session_state.quick_action == "search":
        st.session_state.quick_action = None
        st.rerun()
    elif st.session_state.quick_action == "history":
        st.session_state.quick_action = None
        st.rerun()

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        MedInsight | 
        Built with Streamlit | 
        Current Patient: <strong>{}</strong>
    </div>
""".format(st.session_state.patient_id), unsafe_allow_html=True)
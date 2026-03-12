"""
MedInsight - Medical Report Diagnosis Agentic System
Streamlit Chatbot UI
"""
import streamlit as st
import time
from pathlib import Path
import tempfile
import os

# ── Page config (MUST be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="MedInsight",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap');

/* ── Root palette ── */
:root {
    --bg-deep:      #0d1117;
    --bg-panel:     #161b22;
    --bg-card:      #1c2430;
    --border:       #30363d;
    --accent:       #2ea8ff;
    --accent-soft:  #1a6fa8;
    --accent-glow:  rgba(46,168,255,0.15);
    --success:      #3fb950;
    --warning:      #d29922;
    --danger:       #f85149;
    --text-primary: #e6edf3;
    --text-muted:   #7d8590;
    --text-dim:     #484f58;
    --bubble-user:  #1f4068;
    --bubble-ai:    #1c2430;
    --radius:       14px;
    --radius-sm:    8px;
}

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-deep) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0;
}

/* ── Main content area ── */
[data-testid="stMain"] {
    background: var(--bg-deep) !important;
}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Chat message bubbles ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.25rem 1.5rem !important;
}
[data-testid="stChatMessage"][data-testid*="user"],
.stChatMessage:has([data-testid="chatAvatarIcon-user"]) {
    background: transparent !important;
}

/* User bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stChatMessageContent {
    background: var(--bubble-user) !important;
    border: 1px solid var(--accent-soft) !important;
    border-radius: var(--radius) var(--radius) 4px var(--radius) !important;
    color: var(--text-primary) !important;
}

/* Assistant bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stChatMessageContent {
    background: var(--bubble-ai) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) var(--radius) var(--radius) 4px !important;
    color: var(--text-primary) !important;
}

.stChatMessageContent {
    padding: 0.85rem 1.1rem !important;
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
}

/* Avatar icons */
[data-testid="chatAvatarIcon-user"] {
    background: var(--accent) !important;
    color: white !important;
}
[data-testid="chatAvatarIcon-assistant"] {
    background: var(--success) !important;
    color: white !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background: var(--bg-panel) !important;
    border-top: 1px solid var(--border) !important;
    padding: 1rem 1.5rem !important;
}
[data-testid="stChatInputTextArea"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
}
[data-testid="stChatInputTextArea"]:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}

/* ── Sidebar elements ── */
.sidebar-logo {
    padding: 1.5rem 1.25rem 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.25rem;
}
.sidebar-logo h1 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 1.7rem !important;
    color: var(--text-primary) !important;
    margin: 0 !important;
    letter-spacing: -0.01em;
}
.sidebar-logo .tagline {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.sidebar-logo .dot {
    color: var(--accent);
}

.sidebar-section-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    padding: 0 1.25rem;
    margin-bottom: 0.5rem;
}

/* Patient badge */
.patient-badge {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: var(--accent-glow);
    border: 1px solid var(--accent-soft);
    border-radius: var(--radius-sm);
    padding: 0.6rem 1rem;
    margin: 0 1.25rem 1.5rem;
}
.patient-badge .pid-label {
    font-size: 0.7rem;
    color: var(--accent);
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.patient-badge .pid-value {
    font-size: 0.9rem;
    color: var(--text-primary);
    font-weight: 500;
}
.patient-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    flex-shrink: 0;
    box-shadow: 0 0 6px var(--success);
}

/* ── Streamlit widgets dark override ── */
.stTextInput > div > div > input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}
.stTextInput label {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 0.45rem 1.1rem !important;
    transition: all 0.15s ease !important;
    width: 100%;
}
.stButton > button:hover {
    background: #1a8fe0 !important;
    box-shadow: 0 4px 14px rgba(46,168,255,0.35) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 0.75rem !important;
    margin: 0 0 1rem !important;
}
[data-testid="stFileUploader"] label {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: var(--text-muted) !important;
}

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1rem 0 !important;
}

/* Tips box */
.tip-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius-sm);
    padding: 0.75rem 1rem;
    margin: 0 1.25rem 1rem;
    font-size: 0.8rem;
    color: var(--text-muted);
    line-height: 1.6;
}
.tip-box strong {
    color: var(--text-primary);
    display: block;
    margin-bottom: 0.35rem;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.tip-box code {
    background: var(--bg-deep);
    color: var(--accent);
    padding: 0.1em 0.35em;
    border-radius: 4px;
    font-size: 0.78rem;
}

/* Chat header bar */
.chat-header {
    background: var(--bg-panel);
    border-bottom: 1px solid var(--border);
    padding: 0.85rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    position: sticky;
    top: 0;
    z-index: 100;
}
.chat-header-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-primary);
}
.chat-header-sub {
    font-size: 0.78rem;
    color: var(--text-muted);
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: 0 0 8px var(--success);
    flex-shrink: 0;
}

/* Empty state */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 55vh;
    text-align: center;
    padding: 2rem;
    color: var(--text-muted);
}
.empty-state .icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.6;
}
.empty-state h2 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.8rem;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}
.empty-state p {
    font-size: 0.9rem;
    max-width: 380px;
    line-height: 1.7;
}

.pill {
    display: inline-block;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.3rem 0.85rem;
    font-size: 0.78rem;
    color: var(--text-muted);
    margin: 0.2rem;
    cursor: default;
}

/* Spinner override */
[data-testid="stSpinner"] {
    color: var(--accent) !important;
}

/* scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-dim); }

/* File chip shown after upload */
.file-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    color: var(--accent);
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ───────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "patient_id" not in st.session_state:
    st.session_state.patient_id = "pt-001"
if "patient_input_val" not in st.session_state:
    st.session_state.patient_input_val = "pt-001"


# ── Helper: detect search intent ────────────────────────────────────────────
def is_search_command(text: str) -> bool:
    keywords = [
        'find doctor', 'find doctors', 'search doctor', 'search doctors',
        'find me a doctor', 'find me doctors', 'look for doctor',
        'recommend doctor', 'recommend doctors', 'need a doctor',
        'show me doctors', 'get doctors', 'locate doctor', '--search',
    ]
    t = text.lower().strip()
    if t == 'search':
        return True
    return any(k in t for k in keywords)


# ── Helper: call backend ─────────────────────────────────────────────────────
def call_backend(user_text: str, uploaded_file=None, patient_id: str = "pt-001") -> str:
    """
    Bridge to the existing workflow functions.
    Swap the body of this function out for real calls once integrated.
    """
    try:
        from graph.workflow import run_report_workflow, run_search_workflow
        from tools.ocr_tools import cleanup_temp_files

        # Doctor search
        if is_search_command(user_text) and uploaded_file is None:
            result = run_search_workflow(patient_id=patient_id)
            return result.get("final_response", "No search results generated.")

        # File upload
        if uploaded_file is not None:
            suffix = Path(uploaded_file.name).suffix.lower()
            if suffix == ".pdf":
                input_type = "pdf"
            elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
                input_type = "image"
            elif suffix in [".mp3", ".wav", ".m4a", ".flac"]:
                input_type = "audio"
            else:
                return f"❌ Unsupported file type: `{suffix}`. Please upload a PDF, image, or audio file."

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            try:
                result = run_report_workflow(
                    input_type=input_type,
                    file_path=tmp_path,
                    patient_id=patient_id,
                )
            finally:
                os.unlink(tmp_path)
                cleanup_temp_files()

            return result.get("final_response", "No response generated.")

        # Plain text
        result = run_report_workflow(
            input_type="text",
            text_input=user_text,
            patient_id=patient_id,
        )
        return result.get("final_response", "No response generated.")

    except ImportError:
        # ── Demo mode (no backend installed) ──────────────────────────────
        time.sleep(1.2)
        if is_search_command(user_text):
            return (
                "🔍 **Doctor Search Results** *(demo mode)*\n\n"
                "Based on your medical report, here are recommended specialists:\n\n"
                "1. **Dr. Anika Sharma** – Cardiologist, Apollo Hospitals, Kolkata\n"
                "   📞 +91-33-2320-3040 · ⭐ 4.8\n\n"
                "2. **Dr. Rajesh Mehta** – General Physician, AMRI Hospitals\n"
                "   📞 +91-33-2454-9000 · ⭐ 4.6\n\n"
                "3. **Dr. Priya Banerjee** – Endocrinologist, Fortis Hospital\n"
                "   📞 +91-33-6628-4444 · ⭐ 4.7\n\n"
                "*Install the full backend to get real results.*"
            )
        if uploaded_file:
            return (
                f"📄 **File received:** `{uploaded_file.name}` *(demo mode)*\n\n"
                "Your medical report has been processed. Here is a summary:\n\n"
                "- **Hemoglobin:** 13.2 g/dL *(normal)*\n"
                "- **Glucose (fasting):** 105 mg/dL *(slightly elevated)*\n"
                "- **Blood Pressure:** 128/82 mmHg *(pre-hypertension range)*\n"
                "- **Cholesterol (total):** 195 mg/dL *(normal)*\n\n"
                "⚠️ Mild glucose and BP elevation noted. Consider lifestyle modifications and follow-up.\n\n"
                "*Install the full backend for real analysis.*"
            )
        return (
            f"💬 **Response** *(demo mode)*\n\n"
            f"You asked: *\"{user_text}\"*\n\n"
            "The backend modules (`graph.workflow`, `tools.ocr_tools`) are not installed in this environment. "
            "This UI is fully wired — just drop it alongside your existing `main.py` and the live responses will flow through automatically.\n\n"
            "*Tip: use `--search` or upload a file to test other flows.*"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="sidebar-logo">
        <h1>Med<span class="dot">Insight</span></h1>
        <div class="tagline">Medical Diagnosis · AI Agent</div>
    </div>
    """, unsafe_allow_html=True)

    # Patient ID section
    st.markdown('<div class="sidebar-section-label">Patient Session</div>', unsafe_allow_html=True)

    pid_input = st.text_input(
        "Patient ID",
        value=st.session_state.patient_input_val,
        placeholder="e.g. pt-001",
        label_visibility="collapsed",
        key="pid_text_input",
    )

    col_apply, col_clear = st.columns([2, 1])
    with col_apply:
        if st.button("Apply Patient ID", key="apply_pid"):
            if pid_input.strip():
                st.session_state.patient_id = pid_input.strip()
                st.session_state.patient_input_val = pid_input.strip()
                st.success(f"Switched to **{pid_input.strip()}**", icon="✓")
            else:
                st.error("Enter a valid ID")
    with col_clear:
        if st.button("Clear", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    # Active patient badge
    st.markdown(f"""
    <div class="patient-badge">
        <div class="patient-dot"></div>
        <div>
            <div class="pid-label">Active Patient</div>
            <div class="pid-value">{st.session_state.patient_id}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    # File uploader
    st.markdown('<div class="sidebar-section-label">Upload Report</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload a medical report",
        type=["pdf", "png", "jpg", "jpeg", "bmp", "tiff", "mp3", "wav", "m4a", "flac"],
        label_visibility="collapsed",
        key="file_uploader",
    )
    if uploaded_file:
        ext = Path(uploaded_file.name).suffix.lower()
        icon = "🖼️" if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"] else ("🎵" if ext in [".mp3", ".wav", ".m4a", ".flac"] else "📄")
        st.markdown(f'<div class="file-chip">{icon} {uploaded_file.name}</div>', unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    # Tips
    st.markdown("""
    <div class="tip-box">
        <strong>💡 Quick commands</strong>
        Type <code>find doctors</code> to search specialists.<br>
        Upload a PDF / image / audio report above, then hit Send.<br>
        Use <code>--search</code> for instant doctor lookup.
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="padding: 0 1.25rem; font-size: 0.72rem; color: var(--text-dim); line-height: 1.6;">
        MedInsight v1.0 · Powered by LangGraph<br>
        Not a substitute for professional medical advice.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN CHAT AREA
# ═══════════════════════════════════════════════════════════════════════════════

# Sticky header
st.markdown(f"""
<div class="chat-header">
    <div class="status-dot"></div>
    <div>
        <div class="chat-header-title">MedInsight Assistant</div>
        <div class="chat-header-sub">Patient: {st.session_state.patient_id} · Ready</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Message history or empty state
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🩺</div>
        <h2>How can I help you today?</h2>
        <p>Upload a medical report, ask about your results, or search for specialist doctors.</p>
        <div style="margin-top:1rem;">
            <span class="pill">📄 Analyse a report</span>
            <span class="pill">🔍 Find doctors</span>
            <span class="pill">💬 Ask a question</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🩺"):
            st.markdown(msg["content"])

# Chat input
prompt = st.chat_input(
    "Ask about your report, search for doctors, or type a query…",
    key="chat_input",
)

if prompt:
    # ── Show user message ──
    display_text = prompt
    if uploaded_file:
        ext = Path(uploaded_file.name).suffix.lower()
        icon = "🖼️" if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"] else ("🎵" if ext in [".mp3", ".wav", ".m4a", ".flac"] else "📄")
        display_text = f"{icon} `{uploaded_file.name}`\n\n{prompt}" if prompt.strip() else f"{icon} `{uploaded_file.name}`"

    st.session_state.messages.append({"role": "user", "content": display_text})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(display_text)

    # ── Generate + stream assistant response ──
    with st.chat_message("assistant", avatar="🩺"):
        placeholder = st.empty()
        with st.spinner("Thinking…"):
            response = call_backend(
                user_text=prompt if prompt.strip() else "Process the uploaded file.",
                uploaded_file=uploaded_file,
                patient_id=st.session_state.patient_id,
            )

        # Typewriter stream effect
        streamed = ""
        for char in response:
            streamed += char
            placeholder.markdown(streamed + "▌")
            time.sleep(0.008)
        placeholder.markdown(streamed)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
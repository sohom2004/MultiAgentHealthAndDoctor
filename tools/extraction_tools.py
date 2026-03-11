import re
import ast
import json
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from config.settings import (
    CHROMA_DIR,
    EMBEDDING_MODEL,
    FINDINGS_COLLECTION
)


def get_next_report_id() -> str:
    """
    Generates the next sequential report ID based on existing findings collection entries.

    Returns:
        Report ID string (e.g., "RPT-1")
    """
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = Chroma(
        collection_name=FINDINGS_COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    results = vector_store.get(include=["metadatas"])

    if not results["metadatas"]:
        return "RPT-1"

    report_ids = [m["report_id"] for m in results["metadatas"] if "report_id" in m]

    if not report_ids:
        return "RPT-1"

    max_id = max(int(r.split("-")[1]) for r in report_ids)
    return f"RPT-{max_id + 1}"


def _parse_input(action_input) -> dict:
    """
    Robustly parses the agent's input string into a dict using multiple strategies.
    Handles: valid JSON, Python literals, unquoted keys, and partial regex extraction.
    """
    if isinstance(action_input, dict):
        return action_input

    raw = str(action_input).strip()
    print(f"[save_findings] raw input: {raw!r}")

    # Strategy 1: standard JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Python literal — handles single-quoted strings and Python booleans
    try:
        return ast.literal_eval(raw)
    except Exception:
        pass

    # Strategy 3: quote bare (unquoted) keys then retry JSON
    # Converts  {findings: [...]}  ->  {"findings": [...]}
    try:
        fixed = re.sub(r'(?<!["\'\w])([a-zA-Z_]\w*)\s*:', r'"\1":', raw)
        return json.loads(fixed)
    except Exception:
        pass

    # Strategy 4: regex field extraction as last resort
    try:
        findings, values, patient_id = [], {}, None

        fm = re.search(r'"?findings"?\s*:\s*(\[.*?\])', raw, re.DOTALL)
        if fm:
            findings = json.loads(fm.group(1))

        vm = re.search(r'"?values"?\s*:\s*(\{.*?\})', raw, re.DOTALL)
        if vm:
            values = json.loads(vm.group(1))

        pm = re.search(r'"?patient_id"?\s*:\s*["\']([^"\']+)["\']', raw)
        if pm:
            patient_id = pm.group(1)

        return {"findings": findings, "values": values, "patient_id": patient_id}
    except Exception:
        pass

    raise ValueError(f"save_findings could not parse input: {raw!r}")


def save_findings(action_input) -> str:
    """
    Generates metadata (report_id, patient_id, upload_date) and saves extracted
    findings and values into the findings ChromaDB collection.

    Args:
        action_input: Dict or string (JSON / Python literal / unquoted-key dict) with:
            - 'findings':   list of finding strings
            - 'values':     dict of key-value medical data
            - 'patient_id': patient identifier

    Returns:
        JSON string of saved metadata: {report_id, patient_id, upload_date}
    """
    parsed = _parse_input(action_input)

    if not isinstance(parsed, dict):
        raise ValueError("save_findings input must resolve to a dict")

    findings   = parsed.get("findings", [])
    values     = parsed.get("values", {})
    patient_id = parsed.get("patient_id")

    if not patient_id:
        raise ValueError("patient_id is required in save_findings input")

    # Metadata is generated here — never read from the document
    report_id   = get_next_report_id()
    upload_date = datetime.now().date().isoformat()

    metadata = {
        "report_id":   report_id,
        "patient_id":  patient_id,
        "upload_date": upload_date,
    }

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = Chroma(
        collection_name=FINDINGS_COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    document = Document(
        page_content=json.dumps(
            {"findings": findings, "values": values},
            ensure_ascii=False
        ),
        metadata=metadata
    )

    vector_store.add_documents(documents=[document])
    print(f"Saved findings for report {report_id} (patient: {patient_id}, date: {upload_date})")
    return json.dumps(metadata)
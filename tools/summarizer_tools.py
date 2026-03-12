import json
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from config.settings import (
    CHROMA_DIR,
    EMBEDDING_MODEL,
    FINDINGS_COLLECTION,
    SUMMARY_COLLECTION
)

MAX_COMPARISON_FINDINGS = 5


def get_all_findings(user_id: str) -> list:
    """
    Retrieves the most recent MAX_COMPARISON_FINDINGS (5) findings for a patient,
    sorted oldest-to-newest so the summarizer receives them in chronological order
    (latest last, matching the existing summarizer_agent.py convention of
    reports[-1] = latest, reports[:-1] = history).

    Args:
        user_id: Patient ID

    Returns:
        List of up to 5 finding dicts, oldest first
    """
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = Chroma(
        collection_name=FINDINGS_COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    results = vector_store.get(
        where={"patient_id": user_id},
        include=["documents", "metadatas"]
    )

    raw_docs      = results.get("documents", [])
    raw_metadatas = results.get("metadatas", [])
    raw_ids       = results.get("ids", [])

    # Pair documents with their metadata so we can sort by date + insertion order
    paired = list(zip(raw_ids, raw_docs, raw_metadatas))

    # Sort oldest → newest: primary key = upload_date, tiebreak = insertion index
    paired.sort(key=lambda x: (x[2].get("upload_date", ""), raw_ids.index(x[0])))

    # Keep only the most recent MAX_COMPARISON_FINDINGS entries
    recent = paired[-MAX_COMPARISON_FINDINGS:]

    docs = []
    for _, doc_content, _ in recent:
        try:
            docs.append(json.loads(doc_content))
        except Exception:
            continue

    print(f"Retrieved {len(docs)} recent finding(s) (of {len(paired)} total) "
          f"for patient {user_id}")
    return docs


def get_recent_findings(user_id: str) -> dict:
    """
    Retrieves the single most recent finding for a patient.

    Args:
        user_id: Patient ID

    Returns:
        Most recent finding dict, or empty dict if none found
    """
    findings = get_all_findings(user_id)
    return findings[-1] if findings else {}


def store_summaries(summary: str, user_id: str):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = Chroma(
        collection_name=SUMMARY_COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )
    current_date      = datetime.now().strftime("%Y-%m-%d")
    current_timestamp = datetime.now().isoformat()

    document = Document(
        page_content=summary,
        metadata={
            "user_id":    user_id,
            "date":       current_date,
            "timestamp":  current_timestamp
        }
    )
    vector_store.add_documents(documents=[document])
    print(f"Saved summary for user {user_id} on {current_date}")
    return "Summaries saved successfully"
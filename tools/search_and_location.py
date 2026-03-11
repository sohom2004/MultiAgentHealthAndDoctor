import requests
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from config.settings import (
    CHROMA_DIR,
    EMBEDDING_MODEL,
    SUMMARY_COLLECTION
)
import re
from typing import Optional

def get_user_location(api_key):
    try:
        ip_response = requests.get("https://api.ipify.org?format=json")
        ip_response.raise_for_status()
        ip = ip_response.json().get("ip")

        geo_url = f"https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}"
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()
        data = geo_response.json()

        location_info = {
            "ip": ip,
            "city": data.get("city"),
            "state_prov": data.get("state_prov"),
            "country": data.get("country_name"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude")
        }

        return location_info

    except Exception as e:
        print("Error fetching location:", e)
        return None


def get_user_summaries(user_id: str) -> Optional[str]:
    """
    Retrieves the most recent medical summary for a given user from ChromaDB.
    
    Args:
        user_id: Patient identifier (e.g., 'pt-007')
        
    Returns:
        Most recent summary document or None if not found
    """
    user_id = clean_user_id(user_id)
    
    if not user_id:
        print("❌ Invalid or empty user_id provided")
        return None
    
    print(f"🔍 Searching for user_id: '{user_id}'")
    
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vector_store = Chroma(
            collection_name=SUMMARY_COLLECTION,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR)
        )
        
        results = vector_store.get(
            where={"user_id": user_id},
            include=["metadatas", "documents"]
        )
        
        print(f"📊 ChromaDB returned {len(results.get('documents', []))} documents")
        
        if not results or not results.get('documents') or len(results['documents']) == 0:
            print(f"❌ No summaries found for user {user_id}")
            
            debug_all_results = vector_store.get(include=["metadatas"])
            existing_user_ids = set(
                meta.get('user_id', '') 
                for meta in debug_all_results.get('metadatas', [])
            )
            print(f"💡 Available user_ids in database: {existing_user_ids}")
            
            return None
        
        documents_with_metadata = list(zip(
            results['documents'],
            results['metadatas']
        ))
        
        sorted_results = sorted(
            documents_with_metadata,
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        
        most_recent_summary = sorted_results[0][0]
        timestamp = sorted_results[0][1].get('timestamp', 'unknown')
        
        print(f"✅ Found summary from {timestamp}")
        print(f"📄 Summary preview: {most_recent_summary[:100]}...")
        
        return most_recent_summary
        
    except Exception as e:
        print(f"❌ Error retrieving summaries: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def clean_user_id(user_id: str) -> str:
    """
    Clean and normalize user_id input to handle malformed inputs.
    
    Args:
        user_id: Raw user_id input (may be malformed)
        
    Returns:
        Cleaned user_id string
    """
    if not user_id:
        return ""
    
    # If input is a JSON string or dict, extract the user_id value
    try:
        if isinstance(user_id, dict):
            return str(user_id.get("user_id", "")).strip()
        if user_id.strip().startswith("{") and user_id.strip().endswith("}"):
            import json
            parsed = json.loads(user_id)
            return str(parsed.get("user_id", "")).strip()
    except Exception:
        pass
    # Otherwise, just strip whitespace
    return str(user_id).strip()

import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

def search(query, key):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        "query": query,
        "key": key
    }
    
    try:
        print(f"Searching for '{query}' using Essentials/Basic tier...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        
        print(f"Found {len(results)} places.\n")
        
        for place in results:
            # These fields are included in the Basic Search response
            name = place.get('name', 'N/A')
            address = place.get('formatted_address', 'N/A')
            rating = place.get('rating', 'N/A')
            user_ratings_total = place.get('user_ratings_total', 0)
            
            # Geometry (Location) is also Basic
            lat = place.get('geometry', {}).get('location', {}).get('lat', 0)
            lng = place.get('geometry', {}).get('location', {}).get('lng', 0)
            
            # Open Status (Basic)
            is_open = "Unknown"
            if 'opening_hours' in place:
                is_open = "Open Now" if place['opening_hours'].get('open_now') else "Closed"

            print(f"--- {name} ---")
            print(f"⭐ Rating: {rating} / 5 ({user_ratings_total} votes)")
            print(f"📍 Address: {address}")
            print(f"🗺️ Coordinates: {lat}, {lng}")
            print(f"🕒 Status: {is_open}")
            print("-" * 30)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

query = "cardiologists in kolkata"
key = os.getenv("key")
search(query=query, key=key)
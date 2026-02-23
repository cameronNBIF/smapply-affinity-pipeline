import os
import requests
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

AFFINITY_BASE_URL = os.environ.get("AFFINITY_BASE_URL", "https://api.affinity.co")
AFFINITY_TOKEN = os.environ.get("AFFINITY_ACCESS_TOKEN")

AFFINITY_HEADERS = {
    "Authorization": f"Bearer {AFFINITY_TOKEN}",
    "Content-Type": "application/json"
}

def get_affinity_list_entries(list_id: str) -> List[Dict]:
    """Get all entries from an Affinity list."""
    url = f"{AFFINITY_BASE_URL}/v2/lists/{list_id}/list-entries"
    params = {"limit": 100}
    all_entries = []
    print("Using version 2")
    while url:
        r = requests.get(url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        params = None
        r.raise_for_status()
        
        payload = r.json()
        all_entries.extend(payload.get("data", []))
        
        pagination = payload.get("pagination", {}) or {}
        next_url = pagination.get("nextUrl")
        
        if next_url:
            url = next_url if next_url.startswith("http") else f"{AFFINITY_BASE_URL}{next_url}"
        else:
            url = None
    
    return all_entries

def get_affinity_list_fields(list_id: str) -> List[Dict]:
    """Get all fields for an Affinity list."""
    url = f"{AFFINITY_BASE_URL}/v2/lists/{list_id}/fields"
    params = {"limit": 100}
    all_fields = []
    
    while url:
        r = requests.get(url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        params = None
        r.raise_for_status()
        
        payload = r.json()
        all_fields.extend(payload.get("data", []))
        
        pagination = payload.get("pagination", {}) or {}
        next_url = pagination.get("nextUrl")
        
        if next_url:
            url = next_url if next_url.startswith("http") else f"{AFFINITY_BASE_URL}{next_url}"
        else:
            url = None
    
    return all_fields

def get_affinity_lists() -> List[Dict]:
    """Fetch all available lists in Affinity."""
    url = f"{AFFINITY_BASE_URL}/v2/lists"
    params = {"limit": 100}
    all_lists = []

    while url:
        r = requests.get(url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        params = None
        r.raise_for_status()
        payload = r.json()
        all_lists.extend(payload.get("data", []))

        pagination = payload.get("pagination", {}) or {}
        next_url = pagination.get("nextUrl")

        if next_url:
            url = next_url if next_url.startswith("http") else f"{AFFINITY_BASE_URL}{next_url}"
        else:
            url = None

    return all_lists
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AFFINITY_BASE_URL = os.environ.get("AFFINITY_BASE_URL", "https://api.affinity.co")
AFFINITY_TOKEN = os.environ.get("AFFINITY_ACCESS_TOKEN")

AFFINITY_HEADERS = {
    "Authorization": f"Bearer {AFFINITY_TOKEN}",
    "Content-Type": "application/json"
}

def find_or_create_person(first_name: str, last_name: str, email: str) -> int:
    if not email:
        return None
        
    search_url = f"{AFFINITY_BASE_URL}/persons"
    params = {"term": email}
    
    try:
        r = requests.get(search_url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        r.raise_for_status()
        results = r.json()
        
        persons_list = results.get("persons", []) if isinstance(results, dict) else results
        if persons_list:
            return persons_list[0]["id"]
            
        payload = {
            "first_name": first_name or "Unknown",
            "last_name": last_name or "Unknown",
            "emails": [email]
        }
        
        r_create = requests.post(search_url, headers=AFFINITY_HEADERS, json=payload, timeout=30)
        r_create.raise_for_status()
        return r_create.json()["id"]
        
    except requests.exceptions.RequestException as e:
        print(f"    [!] Error finding/creating person ({email}): {e}")
        return None

def find_or_create_organization(company_name: str, email: str = None) -> int:
    if not company_name:
        return None
        
    search_url = f"{AFFINITY_BASE_URL}/organizations"
    params = {"term": company_name}
    
    try:
        r = requests.get(search_url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        r.raise_for_status()
        results = r.json()
        
        org_list = results.get("organizations", []) if isinstance(results, dict) else results
        for org in org_list:
            if isinstance(org, dict) and org.get("name", "").strip().lower() == company_name.strip().lower():
                return org["id"]
                
        payload = {"name": company_name}
        free_email_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
        if email and "@" in email:
            domain = email.split("@")[1].strip().lower()
            if domain not in free_email_providers:
                payload["domains"] = [domain]
                
        r_create = requests.post(search_url, headers=AFFINITY_HEADERS, json=payload, timeout=30)
        r_create.raise_for_status()
        return r_create.json()["id"]
        
    except requests.exceptions.RequestException as e:
        print(f"    [!] Error finding/creating company ({company_name}): {e}")
        return None
    
def create_opportunity_list_entry(list_id: str, opp_name: str, org_id: int, person_id: int) -> str:
    """Creates a new Opportunity and returns its list entry ID."""
    url = f"{AFFINITY_BASE_URL}/opportunities"
    
    payload = {
        "name": opp_name,
        "list_id": int(list_id),
        "organizations": [org_id] if org_id else [],
        "persons": [person_id] if person_id else []
    }
    
    try:
        r = requests.post(url, headers=AFFINITY_HEADERS, json=payload, timeout=60) #60 to prevent HTTPSConnectionPool Read Timeout errors
        r.raise_for_status()
        opp_data = r.json()
        
        # Creating an Opportunity automatically generates a List Entry.
        # We must extract the 'list_entry_id' from the returned opportunity object
        # so that our main.py loop can update the custom fields!
        list_entries = opp_data.get("list_entries", [])
        
        if list_entries:
            # Return the ID of the list entry tied to our specific list
            for entry in list_entries:
                if str(entry.get("list_id")) == str(list_id):
                    return str(entry["id"])
            return str(list_entries[0]["id"]) # Fallback
            
        print("    ! Created opportunity, but could not parse list_entry_id from response.")
        return None
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            error_msg = e.response.text
        print(f"    X Error creating Opportunity: {error_msg[:200]}")
        return None
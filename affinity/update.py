import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

AFFINITY_BASE_URL = os.environ.get("AFFINITY_BASE_URL", "https://api.affinity.co")
AFFINITY_TOKEN = os.environ.get("AFFINITY_ACCESS_TOKEN")

AFFINITY_HEADERS = {
    "Authorization": f"Bearer {AFFINITY_TOKEN}",
    "Content-Type": "application/json"
}

def update_affinity_field(list_id: str, list_entry_id: str, field_id: str, value: any, field_type: str) -> bool:
    if pd.isna(value) or str(value).lower() == 'nan' or str(value).strip() == "":
        return True 

    formatted_data = value
    if field_type == 'number':
        formatted_data = float(value)
    elif field_type == 'text':
        formatted_data = str(value)
    elif field_type in ['person', 'company']:
        clean_id = int(float(value))
        formatted_data = {"id": clean_id}
    elif field_type == 'location':
        formatted_data = value
    elif field_type == 'datetime' or field_type == 'date':
        try:
            parsed_date = pd.to_datetime(value)
            if field_type == 'datetime':
                formatted_data = parsed_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                formatted_data = parsed_date.strftime('%Y-%m-%d')
        except Exception:
            print(f"      [!] Skipping invalid date format: '{value}'")
            return True

    url = f"{AFFINITY_BASE_URL}/v2/lists/{list_id}/list-entries/{list_entry_id}/fields"
    payload = {
        "operation": "update-fields",
        "updates": [{"id": field_id, "value": {"type": field_type, "data": formatted_data}}]
    }
    
    try:
        r = requests.patch(url, json=payload, headers=AFFINITY_HEADERS, timeout=30)
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            error_msg = e.response.text
        print(f"      [X] Field Update Error ({field_type}):\n      {error_msg}")
        return False
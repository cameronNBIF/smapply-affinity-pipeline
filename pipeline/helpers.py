import re
import pandas as pd
from affinity.find_or_create import find_or_create_organization, find_or_create_person
from affinity.update import update_affinity_field
from config import AFFINITY_IVF_LIST_ID, FIELD_MAPPING

def safe_str(val, default=None):
    """Safely converts Pandas values to strings, avoiding 'nan' or empty strings."""
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
        return default
    return str(val).strip()

def build_affinity_map(existing_entries) -> dict:
    """Creates a dictionary mapping SMApply IDs to Affinity List Entry IDs by parsing the Opportunity Name."""
    affinity_map = {}
    
    for entry in existing_entries:
        # Navigate to the entity name (Affinity V2 stores it here)
        entity_obj = entry.get('entity', {})
        name = entity_obj.get('name', '')
        
        if not name:
            continue
            
        # We format names as "Company Name (12345678)". 
        # This regex looks for digits surrounded by parentheses at the very end of the string.
        match = re.search(r'\((\d+)\)$', name.strip())
        
        if match:
            # Extract just the numbers from the match
            smapply_id = str(int(match.group(1)))
            affinity_map[smapply_id] = str(entry['id'])
            
    return affinity_map

def process_entities(row) -> dict:
    """Finds or creates all necessary Affinity entities and returns their IDs."""
    entity_ids = {
        'org_id': find_or_create_organization(row.get('CompanyName'), row.get('PIEmail')),
        'person_id': find_or_create_person(row.get('PIFirstName'), row.get('PILastName'), row.get('PIEmail')),
        'contact_id': find_or_create_person(
            row.get('CompanyContactFirstName'), 
            row.get('CompanyContactLastName'), 
            row.get('CompanyContactEmail')
        )
    }
    return entity_ids

def build_location_payload(row) -> dict:
    """Constructs the strict Location dictionary required by Affinity."""
    if pd.isna(row.get('Address')) or str(row.get('Address')).strip() == "":
        return None
        
    return {
        "streetAddress": safe_str(row.get('Address')),
        "city": safe_str(row.get('City')),
        "state": safe_str(row.get('Province')),
        "country": safe_str(row.get('Country'), "Canada"),
        "continent": "North America"
    }

def push_custom_fields(row, list_entry_id) -> list:
    """Iterates over the FIELD_MAPPING config to push all values to Affinity."""
    updated_fields = []
    for smapply_key, mapping in FIELD_MAPPING.items():
        if smapply_key not in row or pd.isna(row[smapply_key]):
            continue
        
        val = row[smapply_key]
        field_id = str(mapping['field_id'])
        field_type = mapping['type']
        
        success = update_affinity_field(AFFINITY_IVF_LIST_ID, list_entry_id, field_id, val, field_type)
        if success:
            updated_fields.append(smapply_key)
            
    return updated_fields
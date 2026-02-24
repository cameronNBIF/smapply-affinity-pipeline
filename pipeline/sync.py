from datetime import datetime
import json
import os
import logging
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()

from config import AFFINITY_IVF_LIST_ID
from affinity.find_or_create import create_opportunity_list_entry, get_cache_stats
from affinity.get import get_affinity_list_entries
from pipeline.helpers import build_affinity_map, build_location_payload, process_entities, push_custom_fields


AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "smapply-affinity-pipeline"
SYNC_BLOB_NAME = "sync_state.json"

def get_sync_blob_client():
    """Helper to initialize the Azure Blob Client for the sync state."""
    if not AZURE_STORAGE_CONNECTION_STRING:
        logging.critical("AZURE_STORAGE_CONNECTION_STRING is missing from environment variables.")
        raise EnvironmentError("Missing Azure Storage connection string.")
    
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    return blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=SYNC_BLOB_NAME)

def sync_ivf_to_affinity(application_df):
    """Orchestrates the Upsert pipeline."""
    logging.info("\n" + "=" * 60)
    logging.info("STARTING AFFINITY UPSERT PIPELINE")
    logging.info("=" * 60)

    logging.info(f"Fetching existing entries from Affinity List {AFFINITY_IVF_LIST_ID}...")
    existing_entries = get_affinity_list_entries(AFFINITY_IVF_LIST_ID)
    affinity_map = build_affinity_map(existing_entries)
    logging.info(f"✓ Found {len(affinity_map)} existing applications tracked in Affinity.\n")
    
    for index, row in application_df.iterrows():
        smapply_id = str(int(row['SMApply_ID']))
        company_display = row.get('CompanyName') or 'Unknown'
        
        # 1. Process Entities
        entities = process_entities(row)
        if entities['org_id']: row['Company_Entity_ID'] = entities['org_id']
        if entities['person_id']: row['PI_Entity_ID'] = entities['person_id']
        if entities['contact_id']: row['Contact_Entity_ID'] = entities['contact_id']

        # 2. Opportunity Routing
        list_entry_id = affinity_map.get(smapply_id)
        is_new_application = False

        if not list_entry_id:
            if not entities['org_id'] and not entities['person_id']:
                logging.info(f"[!] SKIPPED: {company_display} ({smapply_id}) - Lacks Company Name & PI Email.")
                continue
            
            opp_name = f"{company_display} ({smapply_id})"
            list_entry_id = create_opportunity_list_entry(
                AFFINITY_IVF_LIST_ID, opp_name, entities['org_id'], entities['person_id']
            )
            
            if not list_entry_id:
                logging.info(f"[!] FAILED: Could not create Opportunity for {smapply_id}.")
                continue
            
            is_new_application = True

        # 3. Payload Construction
        location_payload = build_location_payload(row)
        if location_payload:
            row['LocationPayload'] = location_payload

        # 4. Push Updates
        updated_fields = push_custom_fields(row, list_entry_id)

        # 5. Logging
        if is_new_application:
            logging.info(f"[+] CREATED: {company_display} (SMA: {smapply_id}) | Opp ID: {list_entry_id}")
        else:
            if updated_fields:
                logging.info(f"[~] UPDATED: {company_display} (SMA: {smapply_id}) | Synced fields: {len(updated_fields)}")
            else:
                logging.info(f"[=] NO CHANGES: {company_display} (SMA: {smapply_id})")

    logging.info("\n" + "=" * 60)
    logging.info(f"CACHE PERFORMANCE: Saved {get_cache_stats()} unnecessary API calls to Affinity!")
    logging.info("PIPELINE SYNC COMPLETE")
    logging.info("=" * 60)

def get_last_sync_time():
    """Retrieves the high-water mark timestamp from Azure Blob Storage."""
    try:
        blob_client = get_sync_blob_client()
        blob_data = blob_client.download_blob().readall()
        data = json.loads(blob_data)
        return datetime.fromisoformat(data.get('last_run_time'))
    except Exception as e:
        # It's totally fine if this fails (e.g., the blob doesn't exist yet). 
        # The script gracefully defaults to a Full Sync.
        logging.info(f"    [!] Error reading state file from Blob: {e}. Defaulting to Full Sync.")
        return None

def update_last_sync_time():
    """Saves the current timestamp as the new high-water mark to Azure Blob Storage."""
    try:
        blob_client = get_sync_blob_client()
        # We strip the microseconds to match SMApply's format exactly (e.g., 2024-03-19T14:28:33)
        state_data = {'last_run_time': datetime.utcnow().isoformat()[:19]}
        
        # upload_blob with overwrite=True creates the file if it doesn't exist, and overwrites if it does!
        blob_client.upload_blob(json.dumps(state_data, indent=4), overwrite=True)
        logging.info("    ✓ Successfully updated High-Water Mark in Azure Blob Storage.")
    except Exception as e:
        logging.error(f"    [!] Failed to update High-Water Mark in Azure Blob Storage: {e}")
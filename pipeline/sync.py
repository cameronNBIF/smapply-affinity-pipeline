from config import AFFINITY_IVF_LIST_ID
from affinity.find_or_create import create_opportunity_list_entry
from affinity.get import get_affinity_list_entries
from pipeline.helpers import build_affinity_map, build_location_payload, process_entities, push_custom_fields

def sync_ivf_to_affinity(application_df):
    """Orchestrates the Upsert pipeline."""
    print("\n" + "=" * 60)
    print("STARTING AFFINITY UPSERT PIPELINE")
    print("=" * 60)

    print(f"Fetching existing entries from Affinity List {AFFINITY_IVF_LIST_ID}...")
    existing_entries = get_affinity_list_entries(AFFINITY_IVF_LIST_ID)
    affinity_map = build_affinity_map(existing_entries)
    print(f"✓ Found {len(affinity_map)} existing applications tracked in Affinity.\n")
    
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
                print(f"[!] SKIPPED: {company_display} ({smapply_id}) - Lacks Company Name & PI Email.")
                continue
            
            opp_name = f"{company_display} ({smapply_id})"
            list_entry_id = create_opportunity_list_entry(
                AFFINITY_IVF_LIST_ID, opp_name, entities['org_id'], entities['person_id']
            )
            
            if not list_entry_id:
                print(f"[!] FAILED: Could not create Opportunity for {smapply_id}.")
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
            print(f"[+] CREATED: {company_display} (SMA: {smapply_id}) | Opp ID: {list_entry_id}")
        else:
            if updated_fields:
                print(f"[~] UPDATED: {company_display} (SMA: {smapply_id}) | Synced fields: {len(updated_fields)}")
            else:
                print(f"[=] NO CHANGES: {company_display} (SMA: {smapply_id})")

    print("\n" + "=" * 60)
    print("PIPELINE SYNC COMPLETE")
    print("=" * 60)
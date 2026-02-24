import logging
from datetime import datetime
import pandas as pd
import time
from smapply.program import get_program_ID, get_program_applications, filter_program_applications, process_program_applications
from pipeline.sync import sync_ivf_to_affinity, get_last_sync_time, update_last_sync_time

def main():
    logging.basicConfig(level=logging.INFO)

    logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
    logging.getLogger('azure.storage.blob').setLevel(logging.WARNING)
    
    total_start = time.time()
    
    logging.info("Fetching IVF Program ID")
    ivf_program_id = get_program_ID('Innovation Voucher Fund')
    
    logging.info("Fetching raw applications from SurveyMonkey Apply")
    responses = get_program_applications(ivf_program_id)
    
    logging.info("Filtering and extracting data...")
    all_applications_full = filter_program_applications(responses) 
    
    if not all_applications_full:
        logging.error("\nERROR: No applications found in SurveyMonkey Apply!")
        return
        
    last_sync = get_last_sync_time()
    all_applications = []
    
    if last_sync:
        logging.info(f"    ✓ Found High-Water Mark: {last_sync}. Filtering for recent changes...")
        for app in all_applications_full:
            app_updated_str = app.get('updated_at')
            if app_updated_str:
                # parse the string from SMApply into a datetime object
                app_time = datetime.fromisoformat(app_updated_str)
                if app_time > last_sync:
                    all_applications.append(app)
    else:
        logging.info("    ! No High-Water Mark found. Executing FULL SYNC.")
        all_applications = all_applications_full

    if not all_applications:
        logging.info("\n" + "=" * 60)
        logging.info("PIPELINE SYNC COMPLETE: No new updates to process!")
        logging.info("=" * 60)
        update_last_sync_time()
        return
        
    logging.info(f"✓ Successfully extracted {len(all_applications)} applications. Processing fields:")
    
    sma_start = time.time()
    inv_df, ppl_df, co_df = process_program_applications(all_applications)
    sma_end = time.time()
    logging.info(f"[PROFILER] SurveyMonkey Apply processing took: {sma_end - sma_start:.2f} seconds")
    
    application_df = pd.concat([inv_df, ppl_df, co_df], axis=1)
    application_df = application_df.loc[:, ~application_df.columns.duplicated()]
    
    affinity_start = time.time()
    sync_ivf_to_affinity(application_df)
    affinity_end = time.time()
    logging.info(f"[PROFILER] Affinity Sync took: {affinity_end - affinity_start:.2f} seconds")
    
    # Save the successful run time
    update_last_sync_time()
    
    total_end = time.time()
    logging.info(f"[PROFILER] Total Pipeline Execution Time: {total_end - total_start:.2f} seconds")

if __name__ == "__main__":
    main()
from smapply.tasks import get_application_task, get_application_task_ID, get_application_tasks
from smapply.tables import get_investment, get_people_info, get_voucher_company
from smapply.client import get_paginated, get_session, load_api_info, refresh_token
from config import NUMERIC_COLUMNS
import pandas as pd
import concurrent.futures
import logging


def get_program_ID(name):
    data = load_api_info()
    session = get_session(data)
    base_url = "https://nbif-finb.smapply.io/api/"
    endpoint = 'programs'
    params = None

    responses = get_paginated(session, base_url, endpoint, params)
    if responses is None:
        data = refresh_token(data)
        session = get_session(data)
        responses = get_paginated(session, base_url, endpoint, params)

    for page in responses:
        for result in page.get('results', []):
            if result['name'].strip().lower() == name.strip().lower():
                return result['id']

def get_program_applications(id):
    data = load_api_info()
    session = get_session(data)
    base_url = "https://nbif-finb.smapply.io/api/"
    endpoint = 'applications'
    params = {
        'program': id,
    }

    responses = get_paginated(session, base_url, endpoint, params)
    if responses is None:
        data = refresh_token(data)
        session = get_session(data)
        responses = get_paginated(session, base_url, endpoint, params)
    return responses

def filter_program_applications(responses):
    applications = []
    for page in responses:
        for result in page.get('results', []):
            applications.append(result)
    return applications

def process_program_applications(applications):
    investment_data = []
    people_info_data = []
    voucher_company_data = []

    logging.info(f"Launching multithreaded extraction for {len(applications)} applications...")
    
    # Use ThreadPoolExecutor to fetch data concurrently
    # max_workers=10 is a safe speed limit so SurveyMonkey doesn't block us for spamming
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Map the helper function to all applications
        results = list(executor.map(_process_single_application, applications))

    # Unpack the threaded results back into our lists
    for inv, ppl, vou in results:
        if inv: 
            investment_data.append(inv)
        people_info_data.append(ppl)
        voucher_company_data.append(vou)

    # Convert to DataFrames
    investment_df = pd.DataFrame(investment_data)
    people_info_df = pd.DataFrame(people_info_data)
    voucher_company_df = pd.DataFrame(voucher_company_data)

    # Coerce numerics for the investment data
    numeric_cols = ['AmtRqstd', 'AmtAwarded', 'TotalLevAmt', 'PrivSectorLev']
    for col in numeric_cols:
        if col in investment_df.columns:
            investment_df[col] = pd.to_numeric(investment_df[col], errors='coerce')
            
    # Return all three DataFrames as a tuple
    return investment_df, people_info_df, voucher_company_df

def _process_single_application(application):
    """Helper function to process a single application so we can thread it."""
    id = application['id']
    
    investment_dict = {}
    people_dict = {}
    voucher_dict = {}

    tasks = get_application_tasks(id)
    
    # Get Application Form Task
    application_form_id = get_application_task_ID(tasks, 'IVF - Application Form')
    application_form_task = get_application_task(id, application_form_id) if application_form_id else None

    # 1. Process Investment Data
    app_dict = get_investment(application, tasks, application_form_task, id)
    if app_dict:
        investment_dict = app_dict

    # 2. Process People and Company Data (only if the form task exists)
    if application_form_task:
        people_dict = get_people_info(application_form_task)
        voucher_dict = get_voucher_company(application_form_task)
    else:
        # Keep empty dicts to align rows horizontally
        people_dict = {}
        voucher_dict = {}
        
    return investment_dict, people_dict, voucher_dict
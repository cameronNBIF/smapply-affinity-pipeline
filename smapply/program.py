from smapply.tasks import get_application_task, get_application_task_ID, get_application_tasks
from smapply.tables import get_investment, get_people_info, get_voucher_company
from smapply.client import get_paginated, get_session, load_api_info, refresh_token
from config import NUMERIC_COLUMNS
import pandas as pd


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

    for application in applications:
        id = application['id']
        if id % 10 == 0:
            print(f"Processing application ID: {id}")
        tasks = get_application_tasks(id)
        
        # Get Application Form Task
        application_form_id = get_application_task_ID(tasks, 'IVF - Application Form')
        application_form_task = get_application_task(id, application_form_id) if application_form_id else None

        # 1. Process Investment Data
        app_dict = get_investment(application, tasks, application_form_task, id)
        if app_dict:
            investment_data.append(app_dict)

        # 2. Process People and Company Data (only if the form task exists)
        if application_form_task:
            people_info_data.append(get_people_info(application_form_task))
            voucher_company_data.append(get_voucher_company(application_form_task))
        else:
            # Append empty dicts to keep the rows aligned horizontally
            people_info_data.append({})
            voucher_company_data.append({})

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
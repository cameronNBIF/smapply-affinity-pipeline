from datetime import datetime
from smapply.tasks import get_application_task, get_application_task_ID, get_task_value
from smapply.mapping import map_fiscal_year, map_selector_of_research
from config import SECTOR_MAPPING, PROVINCE_MAPPING, CITY_TO_REGION_MAPPING
from smapply.utils import clean_email, clean_value
import logging

def get_investment(application, tasks, application_form_task, id):
    if not application:
        logging.info(f"Skipping empty application: {id}")
        return None

    # 1. IDENTIFY THE CURRENT STAGE
    current_stage = application.get('current_stage', {}).get('title', 'Unknown Stage')

    # 2. INITIALIZE BASE DICTIONARY
    app_data = {
        'SMApply_ID': id,
        'Application_ID': application.get('reference_id', ''),
        'CurrentStage': current_stage, 
        'RefNum': '',
        'FiscalYear': '',
        'ResearchFundID': 'IVF',
        'ApplDate': None,
        'ApplTitle': None,
        'ExecSum': None,
        'AmtRqstd': 0.0,
        'NBIFSectorID': None,
        'Email': None,
        'CompanyName': None,
        'DateStart': None,                 
        'AnticipatedCompletionDate': None, 
        'AwardResult': None,
        'AmtAwarded': 0.0,
        'TotalLevAmt': 0.0,
        'PrivSectorLev': 0.0,
    }

    # 3. EXTRACT CUSTOM FIELDS (Handles Stage 2 and 3 data)
    for custom_field in application.get('custom_fields') or []:
        name = custom_field.get('name')
        value = custom_field.get('value')
        
        if name == 'NBIF Reference Number' and value:
            app_data['RefNum'] = value
        elif name == 'Fiscal Year':
            app_data['FiscalYear'] = map_fiscal_year(value)
        elif name == 'Anticipated Award End Date' and value:
            app_data['AnticipatedCompletionDate'] = value

    # 4. EXTRACT STAGE 1 (Always runs if application_form_task exists)
    if application_form_task:
        app_data['ApplTitle'] = get_task_value(application_form_task, 'Project Information: | Title of Project:')
        app_data['ExecSum'] = get_task_value(application_form_task, 'Executive Summary:')
        app_data['AmtRqstd'] = clean_value(get_task_value(application_form_task, 'Requested Contribution from NBIF:'))
        app_data['CompanyName'] = get_task_value(application_form_task, 'Company Information: | Company Name:')
        app_data['DateStart'] = get_task_value(application_form_task, 'Anticipated Project Start Date')
        
        email_response = get_task_value(application_form_task, 'Researcher Information: | PI E-mail Address:')
        if email_response:
            app_data['Email'] = clean_email(email_response.strip().lower())

        selector_of_research_id = get_application_task_ID(tasks, 'Select Sector of Research')
        if selector_of_research_id:
            selector_of_research_task = get_application_task(id, selector_of_research_id)
            app_data['NBIFSectorID'] = map_selector_of_research(selector_of_research_task, SECTOR_MAPPING)

        created_at = application.get('created_at')
        if created_at:
            try:
                app_data['ApplDate'] = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S")
            except (ValueError, TypeError):
                logging.info(f"Unexpected created_at format for application {id}: {created_at}")

    # 5. EXTRACT STAGE 3 SPECIFICS (Only runs if logic_level is high enough)
    decision = application.get('decision') or {}
    
    # In SMA's current API, 'awarded' actually holds the dollar amount string (e.g., "80000")
    awarded_val = decision.get('awarded')
    
    if awarded_val:
        app_data['AwardResult'] = True # If there's a value here, it was awarded
        
        try:
            # We pass the 'awarded' string to clean_value instead of 'amount'
            amount_awarded = clean_value(str(awarded_val))
            app_data['AmtAwarded'] = amount_awarded
            
            # Calculate leverages
            app_data['TotalLevAmt'] = amount_awarded / 4 if amount_awarded > 0 else 0.00
            app_data['PrivSectorLev'] = app_data['TotalLevAmt']
        except Exception as e:
            logging.error(f"Could not clean awarded value for application {id}: {awarded_val} ({e})")
    else:
        app_data['AwardResult'] = False

    return app_data

def get_people_info(application_form_task):
    pi_last_name = get_task_value(application_form_task, 'Researcher Information: | PI Last Name:')
    pi_first_name = get_task_value(application_form_task, 'Researcher Information: | Principal Investigator (PI) First Name:')
    
    # Safely extract and format the PI Email
    pi_email_response = get_task_value(application_form_task, 'Researcher Information: | PI E-mail Address:')
    pi_email = clean_email(pi_email_response.strip().lower()) if pi_email_response else None

    company_contact_last_name = get_task_value(application_form_task, 'Company Contact Information... | Last Name:')
    company_contact_first_name = get_task_value(application_form_task, 'Company Contact Information... | First Name:')
    
    # Safely extract and format the Company Contact Email
    company_contact_email_response = get_task_value(application_form_task, 'Company Contact Information... | E-mail Address:')
    company_contact_email = clean_email(company_contact_email_response.strip().lower()) if company_contact_email_response else None

    people_info = {
        'PILastName': pi_last_name,
        'PIFirstName': pi_first_name,
        'PIEmail': pi_email,
        'CompanyContactLastName': company_contact_last_name,
        'CompanyContactFirstName': company_contact_first_name,
        'CompanyContactEmail': company_contact_email,
        'Phone': None,
        'Note': None,
        'CommOptOut': None
    }

    return people_info

def get_voucher_company(application_form_task):
    company_name = get_task_value(application_form_task, 'Company Information: | Company Name:')
    address = get_task_value(application_form_task, 'Company Information: | Company Street Address:')
    city = get_task_value(application_form_task, 'Company Information: | City:')
    postal_code = get_task_value(application_form_task, 'Company Information: | Postal Code:')
    
    # Safely extract and format the Incorporation Date
    incorporation_date_response = get_task_value(application_form_task, 'Company Information: | Date of Incorporation:')
    incorporation_date = incorporation_date_response.replace('/', '-') if incorporation_date_response else None

    voucher_company = {
        'CompanyName': company_name,
        'Address': address,
        'City': city,
        #'Province': province,
        'PostalCode': postal_code,
        'Country': 'Canada',
        'IncorporationDate': incorporation_date#,
        #'Region': region
    }

    return voucher_company
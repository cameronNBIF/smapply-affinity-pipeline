import pandas as pd
from smapply.program import get_program_ID, get_program_applications, filter_program_applications, process_program_applications
from pipeline.sync import sync_ivf_to_affinity

def main():
    print("Fetching IVF Program ID")
    ivf_program_id = get_program_ID('Innovation Voucher Fund')
    
    print("Fetching raw applications from SurveyMonkey Apply")
    responses = get_program_applications(ivf_program_id)
    
    print("Filtering and extracting data")
    all_applications = filter_program_applications(responses) 
    
    if not all_applications:
        print("\nERROR: No applications found in SurveyMonkey Apply!")
        return
        
    print(f"✓ Successfully extracted {len(all_applications)} applications. Processing fields")
    
    #Process into our cleaned DataFrames
    inv_df, ppl_df, co_df = process_program_applications(all_applications)
    
    #Combine horizontally and drop duplicates
    application_df = pd.concat([inv_df, ppl_df, co_df], axis=1)
    application_df = application_df.loc[:, ~application_df.columns.duplicated()]
    
    sync_ivf_to_affinity(application_df)

if __name__ == "__main__":
    main()
import pandas as pd
import re
import time
import sys
import readchar
from config import YEARS, REGIONS

def assignment_exists(table_name, refnum, entity_id, conn):
    """Check if an association already exists in the join table."""
    cursor = conn.cursor()
    if table_name == "staging.ProjectAsgmt":
        cursor.execute("SELECT 1 FROM staging.ProjectAsgmt WHERE RefNum = ? AND PersonID = ?", (refnum, entity_id))
    else:
        cursor.execute("SELECT 1 FROM staging.CompanyAsgmt WHERE RefNum = ? AND CompanyID = ?", (refnum, entity_id))
    return cursor.fetchone() is not None

def safe_int(val):
    """Convert to int if it's a real number, otherwise return None."""
    try:
        if val is None:
            return None
        if pd.isna(val):
            return None
        return int(val)
    except (ValueError, TypeError):
        return None

def remove_duplicates(df):
    df.drop_duplicates(inplace=True)
    return df

def clean_email(email_response):
    if not email_response or not isinstance(email_response, str):
        return None
    
    # Common regex for email detection
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    email = re.search(email_pattern, email_response)
    if email:
        return email.group(0).lower().strip()
    return None

def clean_value(string_value):
    if string_value is None:
        return 0.0
    if isinstance(string_value, (int, float)):
        return float(string_value)
    try:
        s = str(string_value)
        for old, new in [(",", ""), ("$", "")]:
            s = s.replace(old, new)
        return float(s)
    except (ValueError, TypeError):
        return 0.0
    
def choose_fiscal_year():
    YEARS
    index = 0
    while True:
        print(f"\rSelect year: {YEARS[index]}  ", end="", flush=True)
        
        key = readchar.readkey()
        
        if key == readchar.key.RIGHT or key == readchar.key.DOWN or key == " ":
            index = (index + 1) % len(YEARS)
        elif key == readchar.key.LEFT or key == readchar.key.UP:
            index = (index - 1) % len(YEARS)
        elif key == readchar.key.ENTER:
            print()
            return YEARS[index]

def choose_region(city):
    REGIONS
    index = 0
    while True:
        print(f"\rEnter region for city '{city}': {REGIONS[index]}  ", end="", flush=True)
        
        key = readchar.readkey()
        
        if key == readchar.key.RIGHT or key == readchar.key.DOWN or key == " ":
            index = (index + 1) % len(REGIONS)
        elif key == readchar.key.LEFT or key == readchar.key.UP:
            index = (index - 1) % len(REGIONS)
        elif key == readchar.key.ENTER:
            print()
            return REGIONS[index]
import pytest
from unittest.mock import patch
from datetime import datetime
from smapply.tables import get_investment, get_people_info, get_voucher_company

# ==========================================
# 1. FIXTURES (Our Reusable Fake Data)
# ==========================================

@pytest.fixture
def fake_application():
    """A fake top-level application dictionary."""
    return {
        "id": 123456,
        "reference_id": "IVF-00001",
        "current_stage": {"title": "Stage 3: Final Decision"},
        "created_at": "2024-03-19T14:28:33",
        "custom_fields": [
            {"name": "NBIF Reference Number", "value": "IVF_2024_001"},
            {"name": "Fiscal Year", "value": "2024"},
            {"name": "Anticipated Award End Date", "value": "2025-12-31"}
        ],
        "decision": {
            "awarded": "80000" # SMA returns string numbers
        }
    }

@pytest.fixture
def fake_application_form_task():
    """A fake payload perfectly mimicking the 'IVF - Application Form' task."""
    return [
        {
            "data": {
                "f1": {"label": "Company Information: | Company Name:", "response": "Acme Innovations Inc."},
                "f2": {"label": "Company Information: | Company Street Address:", "response": "123 Innovation Way"},
                "f3": {"label": "Company Information: | City:", "response": "Fredericton"},
                "f4": {"label": "Company Information: | Postal Code:", "response": "E3B 1A1"},
                "f5": {"label": "Company Information: | Date of Incorporation:", "response": "2020/05/15"},
                "f6": {"label": "Researcher Information: | Principal Investigator (PI) First Name:", "response": "John"},
                "f7": {"label": "Researcher Information: | PI Last Name:", "response": "Smith"},
                "f8": {"label": "Researcher Information: | PI E-mail Address:", "response": " JOHN.SMITH@ACME.COM "}, # Intentionally messy email
                "f9": {"label": "Company Contact Information... | First Name:", "response": "Jane"},
                "f10": {"label": "Company Contact Information... | Last Name:", "response": "Doe"},
                "f11": {"label": "Company Contact Information... | E-mail Address:", "response": "jane.doe@acme.com"},
                "f12": {"label": "Project Information: | Title of Project:", "response": "AI Quantum Tractor"},
                "f13": {"label": "Executive Summary:", "response": "This is a great project."},
                "f14": {"label": "Requested Contribution from NBIF:", "response": "50000"},
                "f15": {"label": "Anticipated Project Start Date", "response": "2024-06-01"}
            }
        }
    ]

@pytest.fixture
def fake_tasks_list():
    """A fake list of tasks so get_application_task_ID can find the Sector ID."""
    return [
        {
            "results": [
                {"id": 999, "name": "Select Sector of Research"}
            ]
        }
    ]

# ==========================================
# 2. THE TESTS
# ==========================================

def test_get_people_info(fake_application_form_task):
    result = get_people_info(fake_application_form_task)
    
    # Check basic extraction
    assert result['PIFirstName'] == "John"
    assert result['PILastName'] == "Smith"
    assert result['CompanyContactFirstName'] == "Jane"
    
    # Check if the clean_email utility ran (should be lowercase and stripped)
    assert result['PIEmail'] == "john.smith@acme.com"

def test_get_voucher_company(fake_application_form_task):
    result = get_voucher_company(fake_application_form_task)
    
    assert result['CompanyName'] == "Acme Innovations Inc."
    assert result['City'] == "Fredericton"
    assert result['PostalCode'] == "E3B 1A1"
    
    # Check if the slash replacement logic worked
    assert result['IncorporationDate'] == "2020-05-15"

# We MUST patch get_application_task because tables.py calls it directly!
@patch('smapply.tables.get_application_task')
@patch('smapply.tables.map_selector_of_research') # Patch this so we don't have to define SECTOR_MAPPING
@patch('smapply.tables.clean_value') # Patching utilities ensures we only test the table logic
def test_get_investment_success(mock_clean_value, mock_map_selector, mock_get_task, fake_application, fake_tasks_list, fake_application_form_task):
    # 1. ARRANGE
    application_id = 123456
    mock_get_task.return_value = "Fake Sector Task Data"
    mock_map_selector.return_value = "Information Technology"
    
    # Force clean_value to just return the float of whatever string it's given
    mock_clean_value.side_effect = lambda x: float(x)

    # 2. ACT
    result = get_investment(fake_application, fake_tasks_list, fake_application_form_task, application_id)
    
    # 3. ASSERT
    assert result is not None
    assert result['SMApply_ID'] == 123456
    assert result['CurrentStage'] == "Stage 3: Final Decision"
    assert result['RefNum'] == "IVF_2024_001"
    
    # Check if dates and custom mapping worked
    assert result['FiscalYear'] == "2023-2024" # Mapped from "2024"
    assert isinstance(result['ApplDate'], datetime)
    
    # Check the Stage 1 extractions
    assert result['ApplTitle'] == "AI Quantum Tractor"
    assert result['NBIFSectorID'] == "Information Technology"
    
    # Check the Stage 3 Decision Math!
    assert result['AwardResult'] is True
    assert result['AmtAwarded'] == 80000.0
    assert result['TotalLevAmt'] == 20000.0 # 80000 / 4
    assert result['PrivSectorLev'] == 20000.0

def test_get_investment_empty():
    # If passed an empty application, it should gracefully return None
    assert get_investment({}, [], [], 123456) is None
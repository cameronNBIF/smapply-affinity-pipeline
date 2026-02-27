from unittest.mock import patch
from smapply.program import get_program_ID

# We stack @patch decorators to intercept the external calls.
# Note: They are passed as arguments to the function from BOTTOM to TOP!
@patch('smapply.program.load_api_info')
@patch('smapply.program.get_session')
@patch('smapply.program.get_paginated')
def test_get_program_ID_found(mock_get_paginated, mock_get_session, mock_load_api_info):
    
    # 1. ARRANGE: Set up our fakes
    mock_load_api_info.return_value = {"api": {"access_token": "fake_token"}}
    mock_get_session.return_value = "fake_requests_session_object"
    
    # This is the exact JSON structure get_paginated usually returns from SurveyMonkey!
    fake_sma_response = [
        {
            "results": [
                {"id": 111111, "name": "Fake Scholarship Program"},
                {"id": 277707, "name": "Innovation Voucher Fund"},
                {"id": 999999, "name": "Another Random Program"}
            ]
        }
    ]
    # Tell our mock function to hand back our fake JSON instead of hitting the internet
    mock_get_paginated.return_value = fake_sma_response

    # 2. ACT: Run your actual function
    # It will use the fake data we just injected!
    result_id = get_program_ID("Innovation Voucher Fund")

    # 3. ASSERT: Did your logic work?
    assert result_id == 277707
    
    # BONUS: We can even verify that your code actually tried to call the API!
    mock_get_paginated.assert_called_once()


@patch('smapply.program.load_api_info')
@patch('smapply.program.get_session')
@patch('smapply.program.get_paginated')
def test_get_program_ID_not_found(mock_get_paginated, mock_get_session, mock_load_api_info):
    # 1. ARRANGE
    mock_load_api_info.return_value = {}
    mock_get_session.return_value = "fake_session"
    
    # What if SurveyMonkey returns an empty list?
    mock_get_paginated.return_value = [{"results": []}]

    # 2. ACT
    result_id = get_program_ID("Innovation Voucher Fund")

    # 3. ASSERT: Your function should safely return None if it doesn't find a match
    assert result_id is None
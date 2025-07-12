import pytest
from email_validator import validate_email  # Adjust the import based on your actual function name

@pytest.mark.parametrize("email_input, expected_output", [
    ('test@example.com', True),  # Test for valid email with standard format
    ('test.example.com', False),  # Test for email missing '@' symbol
    ('test@@example.com', False),  # Test for email with multiple '@' symbols
    ('test@example', False),  # Test for email with '@' but no '.' after it
    ('@example.com', False),  # Test for email with only '@' symbol
    ('example.com', False),  # Test for email with only a domain
    ('', False)  # Test for empty string as input
])
def test_email_validator(email_input, expected_output):
    assert validate_email(email_input) == expected_output

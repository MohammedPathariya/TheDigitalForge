# Final Report on Email Validation Function Development

## Summary of the Development Process
The project aimed to develop a Python function named `is_valid_email` that verifies the format of email addresses based on specified validation criteria. The initial brief clearly outlined the requirements, which included ensuring the presence of exactly one '@' symbol and at least one '.' character following the '@'. 

Throughout the development process, we maintained close adherence to these requirements, with successful implementation and testing phases.

## Final Outcome
All tests passed successfully.

### Final Code
```python
def is_valid_email(email: str) -> bool:
    # Check if there is exactly one '@' symbol
    if email.count('@') != 1:
        return False
    
    at_index = email.index('@')
    # Ensure there is at least one '.' following the '@'
    if '.' not in email[at_index:]:
        return False
    
    return True
```

### Test Suite
```python
import pytest
from email_validator import is_valid_email


def test_valid_email_formats():
    assert is_valid_email('user@example.com') == True


def test_missing_at_symbol():
    assert is_valid_email('user.example.com') == False


def test_multiple_at_symbols():
    assert is_valid_email('user@@example.com') == False


def test_missing_dot_after_at():
    assert is_valid_email('user@example') == False


def test_valid_email_with_subdomains():
    assert is_valid_email('user@mail.example.com') == True


def test_edge_case_empty_string():
    assert is_valid_email('') == False


def test_mixed_case_in_emails():
    assert is_valid_email('User@ExamPle.com') == True
```
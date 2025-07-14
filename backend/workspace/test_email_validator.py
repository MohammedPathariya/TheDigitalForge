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

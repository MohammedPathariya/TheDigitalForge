import pytest
from email_validator import is_valid_email

def test_valid_email():
    assert is_valid_email('test@example.com') is True


def test_multiple_at_symbols():
    assert is_valid_email('test@@example.com') is False


def test_missing_at_symbol():
    assert is_valid_email('test.example.com') is False


def test_missing_dot_after_at():
    assert is_valid_email('test@domain') is False


def test_empty_string():
    assert is_valid_email('') is False


def test_string_without_at_or_dot():
    assert is_valid_email('test') is False


def test_valid_email_short_domain():
    assert is_valid_email('a@b.co') is True


def test_valid_email_long_domain():
    assert is_valid_email('user.name@verylongdomainname.com') is True
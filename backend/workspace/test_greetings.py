import pytest
from greetings import get_greeting

def test_get_greeting_admin():
    # Test for the name 'Admin'.
    result = get_greeting('Admin')
    expected_output = 'Welcome, Admin!'
    assert result == expected_output, f"Expected '{expected_output}' but got '{result}'"

def test_get_greeting_john():
    # Test for a regular name 'John'.
    result = get_greeting('John')
    expected_output = 'Hello, John!'
    assert result == expected_output, f"Expected '{expected_output}' but got '{result}'"

def test_get_greeting_alice():
    # Test for a regular name 'Alice'.
    result = get_greeting('Alice')
    expected_output = 'Hello, Alice!'
    assert result == expected_output, f"Expected '{expected_output}' but got '{result}'"

def test_get_greeting_empty():
    # Test for an empty string as name.
    result = get_greeting('')
    expected_output = 'Hello, !'
    assert result == expected_output, f"Expected '{expected_output}' but got '{result}'"
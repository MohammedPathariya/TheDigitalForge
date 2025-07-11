import pytest
from list_helpers import find_max  # Adjust the import based on your actual function

def test_valid_input_with_mixed_numbers():
    input_data = [3, 1.5, 2, 4.7]
    expected_output = 4.7
    assert find_max(input_data) == expected_output

def test_valid_input_with_negative_and_positive_numbers():
    input_data = [-1, -5, -3]
    expected_output = -1
    assert find_max(input_data) == expected_output

def test_valid_input_with_single_element():
    input_data = [42]
    expected_output = 42
    assert find_max(input_data) == expected_output

def test_empty_input_list():
    input_data = []
    expected_output = None
    assert find_max(input_data) == expected_output
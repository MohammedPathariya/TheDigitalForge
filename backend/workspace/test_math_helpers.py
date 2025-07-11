import pytest
from math_helpers import your_function_name

# Test for valid input with non-empty list.
def test_valid_input():
    assert your_function_name([1, 2, 3, 4, 5]) == 3.0

# Test with floats in the input list.
def test_floats_input():
    assert your_function_name([1.5, 2.5, 3.5]) == 2.5

# Test with a single number in the list.
def test_single_input():
    assert your_function_name([10]) == 10.0

# Test for handling of an empty list.
def test_empty_list():
    with pytest.raises(ValueError) as excinfo:
        your_function_name([])
    assert str(excinfo.value) == 'Input list cannot be empty'
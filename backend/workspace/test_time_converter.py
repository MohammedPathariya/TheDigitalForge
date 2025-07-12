import pytest
from time_converter import minutes_to_seconds

def test_conversion_of_valid_minute_values_to_seconds():
    assert minutes_to_seconds(5) == 300

def test_conversion_of_edge_case_with_zero_minutes():
    assert minutes_to_seconds(0) == 0

def test_handling_of_negative_input():
    with pytest.raises(ValueError):
        minutes_to_seconds(-1)

def test_conversion_of_large_integer_value():
    assert minutes_to_seconds(1000000) == 60000000

def test_handling_of_non_integer_inputs():
    with pytest.raises(TypeError):
        minutes_to_seconds('5')
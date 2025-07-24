import pytest
from time_converter import minutes_to_seconds

def test_valid_conversion():
    assert minutes_to_seconds(5) == 300
    assert minutes_to_seconds(10) == 600


def test_zero_input():
    assert minutes_to_seconds(0) == 0


def test_negative_input():
    with pytest.raises(ValueError):
        minutes_to_seconds(-5)


def test_large_input():
    assert minutes_to_seconds(100000) == 6000000

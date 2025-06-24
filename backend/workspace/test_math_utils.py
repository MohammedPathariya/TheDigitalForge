import pytest
from math_utils import factorial

def test_factorial_valid_input_5():
    assert factorial(5) == 120

def test_factorial_valid_input_0():
    assert factorial(0) == 1

def test_factorial_invalid_input_negative():
    with pytest.raises(ValueError):
        factorial(-1)

def test_factorial_valid_input_1():
    assert factorial(1) == 1

def test_factorial_valid_input_10():
    assert factorial(10) == 3628800

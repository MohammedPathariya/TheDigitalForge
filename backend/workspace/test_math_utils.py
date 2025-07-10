# test_math_utils.py

import pytest
from math_utils import factorial_function  # Assuming the function's name is 'factorial_function'

def test_factorial_input_0():
    assert factorial_function(0) == 1

def test_factorial_input_1():
    assert factorial_function(1) == 1

def test_factorial_input_5():
    assert factorial_function(5) == 120

def test_factorial_input_3():
    assert factorial_function(3) == 6

def test_factorial_negative_input():
    with pytest.raises(ValueError):
        factorial_function(-1)

def test_factorial_non_integer_input():
    with pytest.raises(ValueError):
        factorial_function(2.5)
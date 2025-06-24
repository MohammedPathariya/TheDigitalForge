import pytest
from math_utils import calculate_factorial


def test_calculate_factorial():
    # Valid input tests
    assert calculate_factorial(0) == 1, 'Failed on valid input: 0'
    assert calculate_factorial(5) == 120, 'Failed on valid input: 5'
    assert calculate_factorial(1) == 1, 'Failed on valid input: 1'
    assert calculate_factorial(10) == 3628800, 'Failed on valid input: 10'

    # Invalid input tests
    with pytest.raises(ValueError, match='Input must be a non-negative integer.'):
        calculate_factorial(-1)
    with pytest.raises(ValueError, match='Input must be a non-negative integer.'):
        calculate_factorial(-5)
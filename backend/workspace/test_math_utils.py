import pytest
from math_utils import calculate_factorial

# Test cases based on the provided testing plan
def test_calculate_factorial():
    # Test for valid input when input is 0.
    assert calculate_factorial(0) == 1, 'Expected output for factorial(0) is 1'
    
    # Test for valid input when input is 1.
    assert calculate_factorial(1) == 1, 'Expected output for factorial(1) is 1'
    
    # Test for valid input when input is 5.
    assert calculate_factorial(5) == 120, 'Expected output for factorial(5) is 120'
    
    # Test for valid input when input is 10.
    assert calculate_factorial(10) == 3628800, 'Expected output for factorial(10) is 3628800'
    
    # Test for handling of edge case when input is a negative integer.
    with pytest.raises(ValueError):
        calculate_factorial(-1)
        
    # Test for handling of edge case when input is a non-integer (e.g., 'a', 5.5).
    with pytest.raises(ValueError):
        calculate_factorial('a')
    with pytest.raises(ValueError):
        calculate_factorial(5.5)

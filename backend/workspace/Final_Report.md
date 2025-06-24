# Development Report for `calculate_factorial` Function

## Summary of Development Process
In this project, we aimed to create a Python function called `calculate_factorial` that accurately computes the factorial of a non-negative integer, as detailed in the initial brief. The development process adhered closely to the specified requirements, ensuring that the function could handle valid inputs and edge cases effectively. The function has been implemented in the `math_utils.py` file and was thoroughly tested to validate its correctness, ensuring a robust solution that meets the project's objectives.

## Final Python Code for `calculate_factorial`
The final implementation of the `calculate_factorial` function is as follows:

```python
def calculate_factorial(n: int) -> int:
    """
    A non-negative integer for which the factorial is to be calculated.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return 1
    factorial = 1
    for i in range(1, n + 1):
        factorial *= i
    return factorial
```

## Complete Test Suite for `calculate_factorial`
The following test suite validates the functionality of the `calculate_factorial` function using `pytest`:

```python
import pytest
from math_utils import calculate_factorial

def test_factorial_of_non_negative_integer_5():
    result = calculate_factorial(5)
    assert result == 120, f"Expected 120 but got {result}"

def test_factorial_of_0():
    result = calculate_factorial(0)
    assert result == 1, f"Expected 1 but got {result}"

def test_factorial_of_negative_integer():
    with pytest.raises(ValueError):
        calculate_factorial(-1)

def test_factorial_of_non_negative_integer_1():
    result = calculate_factorial(1)
    assert result == 1, f"Expected 1 but got {result}"

def test_factorial_of_non_negative_integer_3():
    result = calculate_factorial(3)
    assert result == 6, f"Expected 6 but got {result}"
```

## Conclusion
The `calculate_factorial` function has been implemented and tested, fulfilling all requirements outlined in the initial brief. The tests confirm that the function accurately computes factorials for valid inputs and correctly raises errors for invalid inputs, ensuring a reliable tool for users.
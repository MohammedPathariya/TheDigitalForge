# Final Report for Minutes to Seconds Converter

## Project Overview
This report details the development process and outcomes for the Minutes to Seconds Converter project, as outlined in the initial brief. The primary goal was to create a function that converts a given number of minutes into seconds and handles input validation properly.

## Development Process
The project commenced with the understanding that a function named `minutes_to_seconds` was to be developed within a Python file called `time_converter.py`. The function was required to accept an integer input representing minutes and return the equivalent seconds as an integer. Input validation was also a critical feature, whereby a `ValueError` would be raised for negative inputs.

The development team followed the defined requirements closely throughout the implementation phase. Upon completion, a comprehensive test suite was created using pytest to ensure the function behaved as expected across various scenarios, including valid conversions, zero input, and handling of negative values.

## Final Outcome
All tests passed successfully.

### Python Code
```python
def minutes_to_seconds(minutes: int) -> int:
    if minutes < 0:
        raise ValueError("Input must be a non-negative integer.")
    return minutes * 60
```

### Test Suite
```python
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
```
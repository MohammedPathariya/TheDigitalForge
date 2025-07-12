# Final Report: Convert Minutes to Seconds

## Development Process Summary
The project aimed to create a Python function that accurately converts a given number of minutes into seconds. Starting from the initial brief, we focused on developing the function `minutes_to_seconds`, which successfully handles valid inputs and raises appropriate errors for invalid inputs. The overall development process involved meticulous testing to ensure that the core objectives were met while maintaining code quality.

## Final Outcome
All tests passed successfully.

### Final Code: `time_converter.py`
```python
def minutes_to_seconds(minutes: int) -> int:
    if minutes < 0:
        raise ValueError("Input must be a non-negative integer.")
    return minutes * 60
```

### Complete Test Suite: `test_time_converter.py`
```python
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
```
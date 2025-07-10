import pytest
from number_utils import is_even
\def test_is_even_valid_even_input():
    assert is_even(4) == True
\def test_is_even_valid_odd_input():
    assert is_even(3) == False
\def test_is_even_negative_even_input():
    assert is_even(-2) == True
\def test_is_even_negative_odd_input():
    assert is_even(-5) == False
\def test_is_even_zero_input():
    assert is_even(0) == True
\def test_is_even_string_input():
    with pytest.raises(TypeError):
        is_even('test')
\def test_is_even_float_input():
    with pytest.raises(TypeError):
        is_even(3.5)
\def test_is_even_list_input():
    with pytest.raises(TypeError):
        is_even([2])
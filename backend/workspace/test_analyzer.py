import pytest
from analyzer import count_vowels

def test_count_vowels_normal_string():
    assert count_vowels('Hello World') == 3

def test_count_vowels_case_insensitivity():
    assert count_vowels('HELLO') == 2

def test_count_vowels_empty_string():
    assert count_vowels('') == 0

def test_count_vowels_no_vowels():
    assert count_vowels('bcdfgh') == 0

def test_count_vowels_all_vowels():
    assert count_vowels('AEIOUaeiou') == 10

def test_count_vowels_long_string():
    assert count_vowels('a' * 1000) == 1000

if __name__ == "__main__":
    pytest.main()
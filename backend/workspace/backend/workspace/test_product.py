import pytest
from product import calculate_word_frequency

def test_case_insensitivity():
    assert calculate_word_frequency('Word word WORD') == {'word': 3}

def test_punctuation_ignored():
    assert calculate_word_frequency('Hello, world! Hello.') == {'hello': 2, 'world': 1}

def test_numbers_excluded():
    assert calculate_word_frequency('word 1 word 2') == {'word': 2}

def test_whitespace_handling():
    assert calculate_word_frequency('   hello   world   \n\nhello  ') == {'hello': 2, 'world': 1}

def test_empty_string():
    assert calculate_word_frequency('') == {}

def test_large_input():
    input_string = 'word ' * 1000  # repeating 'word' 1000 times
    assert calculate_word_frequency(input_string) == {'word': 1000}

def test_non_string_input():
    with pytest.raises(ValueError):
        calculate_word_frequency(123)  # should raise an error for non-string input
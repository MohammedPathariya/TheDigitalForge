import pytest
from text_analyzer import analyze_text

def test_normal_input():
    result = analyze_text("This is a test sentence.")
    assert result['word_count'] == 5
    assert result['char_count'] == 30
    assert result['is_question'] is False

def test_empty_string():
    result = analyze_text("")
    assert result['word_count'] == 0
    assert result['char_count'] == 0
    assert result['is_question'] is False

def test_multiple_spaces():
    result = analyze_text("This    is    a    test.")
    assert result['word_count'] == 5
    assert result['char_count'] == 26

def test_question_ending():
    result = analyze_text("Is this a question?")
    assert result['is_question'] is True

def test_no_question():
    result = analyze_text("This is not a question.")
    assert result['is_question'] is False

def test_whitespace_only():
    result = analyze_text("     ")
    assert result['word_count'] == 0
    assert result['char_count'] == 5
    assert result['is_question'] is False
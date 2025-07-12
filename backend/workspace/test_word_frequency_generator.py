import pytest
import os
import csv
from word_frequency_generator import generate_word_frequency  # Assuming your function is in this file

def test_valid_input():
    with open('test_valid.txt', 'w') as f:
        f.write('Hello hello world')
    output_path = 'output.csv'
    generate_word_frequency('test_valid.txt', output_path)
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['word'] == 'hello'
    assert int(rows[0]['count']) == 2
    assert rows[1]['word'] == 'world'
    assert int(rows[1]['count']) == 1
    
    os.remove('test_valid.txt')
    os.remove(output_path)

def test_empty_input_file():
    with open('test_empty.txt', 'w') as f:
        pass  # Creating an empty file
    output_path = 'output_empty.csv'
    generate_word_frequency('test_empty.txt', output_path)

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 0  # No words should be counted
    
    os.remove('test_empty.txt')
    os.remove(output_path)

def test_non_existing_input_file():
    output_path = 'output_non_existing.csv'
    with pytest.raises(FileNotFoundError):
        generate_word_frequency('non_existing.txt', output_path)

def test_input_file_with_punctuation():
    with open('test_punctuation.txt', 'w') as f:
        f.write('Hello, world! Hello world.')
    output_path = 'output_punctuation.csv'
    generate_word_frequency('test_punctuation.txt', output_path)

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]['word'] == 'hello'
    assert int(rows[0]['count']) == 2
    assert rows[1]['word'] == 'world'
    assert int(rows[1]['count']) == 2

    os.remove('test_punctuation.txt')
    os.remove(output_path)

def test_valid_csv_output_format():
    with open('test_format.txt', 'w') as f:
        f.write('word word word')
    output_path = 'output_format.csv'
    generate_word_frequency('test_format.txt', output_path)

    with open(output_path, 'r') as f:
        headers = f.readline().strip().split(',')
        assert headers == ['word', 'count']

    os.remove('test_format.txt')
    os.remove(output_path)

def test_correct_sorting_of_output():
    with open('test_sorting.txt', 'w') as f:
        f.write('banana apple orange apple')
    output_path = 'output_sorting.csv'
    generate_word_frequency('test_sorting.txt', output_path)

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows[0]['word'] == 'apple'
    assert int(rows[0]['count']) == 2
    assert rows[1]['word'] == 'banana'
    assert int(rows[1]['count']) == 1
    assert rows[2]['word'] == 'orange'
    assert int(rows[2]['count']) == 1

    os.remove('test_sorting.txt')
    os.remove(output_path)

def test_output_pathway_validity():
    output_path = 'invalid/output.csv'
    with pytest.raises(Exception):
        generate_word_frequency('test_valid.txt', output_path)

def test_case_insensitivity():
    with open('test_case_insensitivity.txt', 'w') as f:
        f.write('a A a B b B')
    output_path = 'output_case_insensitivity.csv'
    generate_word_frequency('test_case_insensitivity.txt', output_path)

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]['word'] == 'a'
    assert int(rows[0]['count']) == 3
    assert rows[1]['word'] == 'b'
    assert int(rows[1]['count']) == 3

    os.remove('test_case_insensitivity.txt')
    os.remove(output_path)

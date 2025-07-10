import pytest
import os
from csv_utils import read_csv_to_dicts

# Test for valid input
def test_read_valid_csv():
    csv_content = """name,age\nAlice,30\nBob,25"""
    with open('test_valid.csv', 'w') as f:
        f.write(csv_content)
    expected_output = [
        {'name': 'Alice', 'age': '30'},
        {'name': 'Bob', 'age': '25'}
    ]
    assert read_csv_to_dicts('test_valid.csv') == expected_output
    os.remove('test_valid.csv')  # Clean up

# Test for empty file
def test_read_empty_csv():
    with open('test_empty.csv', 'w') as f:
        pass
    with pytest.raises(ValueError):
        read_csv_to_dicts('test_empty.csv')
    os.remove('test_empty.csv')  # Clean up

# Test for file without headers
def test_read_csv_without_headers():
    csv_content = """1,2\n3,4"""
    with open('test_no_headers.csv', 'w') as f:
        f.write(csv_content)
    with pytest.raises(ValueError):
        read_csv_to_dicts('test_no_headers.csv')
    os.remove('test_no_headers.csv')  # Clean up

# Test for non-existent file
def test_read_non_existent_csv():
    with pytest.raises(FileNotFoundError):
        read_csv_to_dicts('non_existent.csv')

# Test for correct data transformation
def test_read_correct_data_transformation():
    csv_content = """name,age\nCharlie,28\nDiana,22"""
    with open('test_data.csv', 'w') as f:
        f.write(csv_content)
    expected_output = [
        {'name': 'Charlie', 'age': '28'},
        {'name': 'Diana', 'age': '22'}
    ]
    assert read_csv_to_dicts('test_data.csv') == expected_output
    os.remove('test_data.csv')  # Clean up

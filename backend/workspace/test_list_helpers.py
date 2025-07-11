import pytest
from list_helpers import find_max

class TestFindMax:
    def test_valid_non_empty_list(self):
        assert find_max([1, 2, 3, 4, 5]) == 5

    def test_valid_non_empty_list_with_floats(self):
        assert find_max([1.1, 2.2, 3.3]) == 3.3

    def test_list_with_integers_and_floats(self):
        assert find_max([1, 5.5, 2]) == 5.5

    def test_empty_list(self):
        assert find_max([]) == None

    def test_list_with_one_number(self):
        assert find_max([42]) == 42

    def test_list_with_negative_numbers(self):
        assert find_max([-1, -5, -3]) == -1
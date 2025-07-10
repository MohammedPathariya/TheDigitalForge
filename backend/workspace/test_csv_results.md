TESTS FAILED:
--- STDOUT ---
.F
=================================== FAILURES ===================================
_____________________________ test_read_empty_csv ______________________________
    def test_read_empty_csv():
        with open('test_empty.csv', 'w') as f:
            pass
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE <class 'ValueError'>

test_csv_utils.py:21: Failed
=========================== short test summary info ============================
FAILED test_csv_utils.py::test_read_empty_csv - Failed: DID NOT RAISE <class ...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 1 passed in 0.05s

--- STDERR ---
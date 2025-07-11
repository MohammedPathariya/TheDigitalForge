TESTS FAILED:
--- STDOUT ---

==================================== ERRORS ====================================
____________________ ERROR collecting test_text_analyzer.py ____________________
../../../../../../anaconda3/envs/digitalforge/lib/python3.10/site-packages/_pytest/python.py:498: in importtestmodule
    mod = import_path(
../../../../../../anaconda3/envs/digitalforge/lib/python3.10/site-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
../../../../../../anaconda3/envs/digitalforge/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1050: in _gcd_import
    ???
<frozen importlib._bootstrap>:1027: in _find_and_load
    ???
<frozen importlib._bootstrap>:1006: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:688: in _load_unlocked
    ???
../../../../../../anaconda3/envs/digitalforge/lib/python3.10/site-packages/_pytest/assertion/rewrite.py:186: in exec_module
    exec(co, module.__dict__)
test_text_analyzer.py:2: in <module>
    from text_analyzer import analyze_text
E     File "/Users/mohammedpathariya/Docs/IUB Docs/Projects/TheDigitalForge/backend/workspace/text_analyzer.py", line 1
E       def analyze_text(text):\n    '''Analyzes the input text and returns a dictionary with various metrics.'''
    if not text: return {}\n    word_count = len(text.split())\n    char_count = len(text)\n    unique_words = len(set(text.split()))\n    return {'word_count': word_count, 'char_count': char_count, 'unique_words': unique_words}
E                               ^
E   SyntaxError: unexpected character after line continuation character
=========================== short test summary info ============================
ERROR test_text_analyzer.py
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.19s

--- STDERR ---
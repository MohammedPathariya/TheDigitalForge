# backend/tasks.py
# CrewAI Task definitions & workflows for Unit 734 - The Digital Forge

from crewai import Task
from agents import unit_734_crew
from tools import file_system_tools

# -----------------------------------------------------------------------------
# DEFINE THE "HAPPY PATH" AND INITIAL SPRINT WORKFLOW
# -----------------------------------------------------------------------------

create_technical_brief = Task(
    description=(
        "Analyze the user request provided below and transform it into a detailed, structured technical brief. "
        "The user's request is: '''{user_request}'''\n\n"
        "Your final output MUST be a Markdown-formatted technical brief that includes these exact sections: "
        "1. Project Overview, 2. Core Objectives, 3. Key Features/Requirements, "
        "4. Constraints, and 5. Success Criteria. "
        "Derive all content for the brief DIRECTLY from the user's request. Do not add or invent any new features."
    ),
    expected_output="A comprehensive, well-structured technical brief in Markdown format that is strictly based on the user's request.",
    agent=unit_734_crew['liaison'],
)

define_development_plan = Task(
    description=(
        "Review the technical brief and deconstruct it into a clear, actionable development plan. "
        "The plan MUST directly correspond to the 'Key Features/Requirements' in the brief.\n\n"
        "Your final output must be a Python dictionary with two keys: 'developer_task' and 'tester_task'.\n"
        "- The 'developer_task' MUST be a precise set of instructions for Hephaestus. It should describe the "
        "function signature (e.g., `def analyze_text(text):`), the logic for case conversion, how to strip "
        "punctuation while preserving apostrophes inside words, and how to filter out standalone numbers.\n"
        "- The 'tester_task' MUST be a precise set of instructions for Argus. It should list the specific pytest "
        "test cases to create (e.g., `test_word_count_simple`, `test_case_insensitivity`, "
        "`test_punctuation_removal`, `test_apostrophe_handling`, `test_number_ignoring`)."
    ),
    expected_output="A Python dictionary with 'developer_task' and 'tester_task' keys, containing specific, actionable instructions derived from the technical brief.",
    agent=unit_734_crew['lead'],
)

# --- CORRECTED TASK 1 ---
generate_python_code = Task(
    description=(
        "Based on the following development plan, write clean, efficient, and correct Python code.\n"
        "Developer Task: '''{developer_task}'''\n\n"
        "First, perform all the cleaning and filtering steps. After cleaning, you MUST split the text into words, "
        "count the frequency of each word, and return the result as a dictionary. "
        "For example: `{{'word': 2, 'another': 1}}`.\n\n"
        "Use the 'save_file' tool to save the generated code to a file named 'product.py'."
    ),
    expected_output="The file path of the saved Python script: 'product.py'.",
    agent=unit_734_crew['developer'],
    tools=file_system_tools,
)

# --- CORRECTED TASK 2 ---
generate_test_suite = Task(
    description=(
        "Based on the following testing plan, create a comprehensive test suite using the pytest framework.\n"
        "Testing Plan: '''{tester_task}'''\n\n"
        "Ensure your tests correctly assert the contents of the returned dictionary. "
        "For example, to test the input 'Test test!', the assertion should be `assert result == {{'test': 2}}`. "
        "Do NOT use `len()` on the result; check the dictionary keys and values directly.\n\n"
        "Use the 'save_file' tool to save the tests to a file named 'test_product.py'."
    ),
    expected_output="The file path of the saved pytest test script: 'test_product.py'.",
    agent=unit_734_crew['tester'],
    tools=file_system_tools,
)

execute_tests = Task(
    description=(
        "Execute the pytest test suite against the generated code using the 'run_tests' tool. "
        "The test file is located at 'test_product.py'. "
        "Analyze the results and provide a definitive summary."
    ),
    expected_output="A string containing the test results: either 'ALL TESTS PASSED' or a detailed, multi-line failure log from pytest.",
    agent=unit_734_crew['tester'],
    tools=file_system_tools,
)

# -----------------------------------------------------------------------------
# DEFINE THE "DEBUGGING" WORKFLOW
# -----------------------------------------------------------------------------

# --- CORRECTED TASK 3 (MOST IMPORTANT) ---
analyze_test_failure = Task(
    description=(
        "Analyze the detailed failure log from the test execution. The log you received is an `AssertionError`. "
        "Your task is to identify the root cause of this specific assertion failure. \n\n"
        "**CRITICAL INSTRUCTION:** Your analysis MUST be grounded ONLY in the provided failure log, the original developer task, "
        "and the existing code. You are forbidden from inventing other errors like `NullReferenceException` or mentioning concepts "
        "like 'user objects', 'login systems', or anything not directly present in the context. "
        "Focus ONLY on the Python code and the `AssertionError`.\n\n"
        "Create a new, clear, and concise 'developer_task' that explains exactly what needs to be fixed in the existing code to "
        "make the failing test pass."
    ),
    expected_output="A new developer_task as a string, precisely describing the bug and the required fix for the given AssertionError.",
    agent=unit_734_crew['lead'],
)

fix_python_code = Task(
    description=(
        "Review the bug report from the Team Lead and the original code. Implement the necessary changes to fix "
        "the bug. You must overwrite the original 'product.py' file with the corrected code using the "
        "'save_file' tool. Ensure the fix is robust and directly addresses the bug report."
    ),
    expected_output="The file path of the newly saved (corrected) Python script: 'product.py'.",
    agent=unit_734_crew['developer'],
    tools=file_system_tools,
)

# -----------------------------------------------------------------------------
# DEFINE THE "FINAL REPORT" WORKFLOW
# -----------------------------------------------------------------------------

compile_final_report = Task(
    description=(
        "Compile a final, client-facing report in Markdown format. The report should include a friendly summary "
        "of the development process. It MUST include the final, verified Python code and the complete test suite "
        "that was used to validate it. \n\n"
        "Use the provided context for the code and tests. Do NOT invent new code.\n\n"
        "Final Code:\n'''\n{final_code}\n'''\n\n"
        "Test Suite:\n'''\n{final_tests}\n'''\n\n"
        "Present the code and tests in clean, readable Python code blocks within the report."
    ),
    expected_output="A comprehensive final report in Markdown format, including a summary, the final code, and the test suite.",
    agent=unit_734_crew['liaison'],
)
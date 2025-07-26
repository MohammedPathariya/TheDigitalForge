# backend/tasks.py
# Generalized CrewAI Task definitions & workflows for The Digital Forge (Robust Version)

from crewai import Task
from agents import unit_734_crew
from tools import file_system_tools

# -----------------------------------------------------------------------------
# SPRINT PLANNING WORKFLOW
# -----------------------------------------------------------------------------

create_technical_brief = Task(
    description=(
        "Analyze the user's request and transform it into a structured technical brief. "
        "Your analysis must be thorough, ensuring all aspects of the request are captured.\n\n"
        "User's Request:\n'''\n{user_request}\n'''\n\n"
        "Your final output MUST be a Markdown-formatted technical brief containing these exact sections: "
        "1. Project Overview, 2. Core Objectives, 3. Key Features & Requirements, "
        "4. Technical Constraints, and 5. Success Criteria. "
        "**CRITICAL:** Derive all content STRICTLY from the user's request. Do NOT add, invent, or assume any new features, technologies, or constraints."
    ),
    expected_output="A comprehensive, well-structured technical brief in Markdown format that is a faithful and complete representation of the user's request.",
    agent=unit_734_crew['liaison'],
)

define_development_plan = Task(
    description=(
        "Review the provided technical brief and deconstruct it into a clear, actionable development plan. "
        "The plan MUST address every item in the 'Key Features & Requirements' and 'Success Criteria' sections of the brief.\n\n"
        "Technical Brief:\n'''\n{technical_brief}\n'''\n\n"
        "Your final output MUST be a single, valid JSON object containing four distinct keys:\n"
        "1. 'file_name': A suitable, PEP8-compliant filename for the Python script (e.g., 'data_processor.py').\n"
        "2. 'test_file_name': A suitable filename for the pytest test suite (e.g., 'test_data_processor.py').\n"
        "3. 'developer_task': A precise set of instructions for the developer. This must detail the required functions, their expected inputs and outputs, and the core logic that needs to be implemented to satisfy the brief.\n"
        "4. 'tester_task': A precise set of instructions for the QA tester. This must describe the testing strategy and list the specific types of test cases needed to validate every feature and success criterion (e.g., 'test for valid input', 'test for handling of edge cases like empty strings', 'test for correct data transformation')."
    ),
    expected_output="A single, valid JSON object with the keys 'file_name', 'test_file_name', 'developer_task', and 'tester_task', containing specific and actionable instructions derived from the technical brief.",
    agent=unit_734_crew['lead'],
)


# -----------------------------------------------------------------------------
# DEVELOPMENT & TESTING WORKFLOW
# -----------------------------------------------------------------------------

generate_python_code = Task(
    description=(
        "Based on the following development task, write clean, efficient, and correct Python code. "
        "You MUST implement the logic exactly as described in the task. Do not add any extra functionality or libraries unless explicitly requested.\n\n"
        "Developer Task:\n'''\n{developer_task}\n'''\n\n"
        "After writing the code, use the 'save_file' tool to save it to the specified filename: {file_name}."
    ),
    expected_output="The full file path of the saved Python script as a string (e.g., 'workspace/data_processor.py').",
    agent=unit_734_crew['developer'],
    tools=file_system_tools,
)

generate_test_suite = Task(
    description=(
        "Based on the following testing plan, create a comprehensive test suite using the pytest framework. "
        "The tests MUST validate the Python code in the file '{file_name}' against all requirements in the testing plan.\n\n"
        "Testing Plan:\n'''\n{tester_task}\n'''\n\n"
        "Your test assertions must be precise and directly check for the expected outcomes. "
        "For example, if a function should return a specific dictionary, assert the contents of the dictionary directly, do not just check its length.\n\n"
        "Use the 'save_file' tool to save the complete test suite to the specified filename: {test_file_name}."
    ),
    expected_output="The full file path of the saved pytest script as a string (e.g., 'workspace/test_data_processor.py').",
    agent=unit_734_crew['tester'],
    tools=file_system_tools,
)

execute_tests = Task(
    description=(
        "Execute the pytest test suite located at '{test_file_name}' against the generated code using the 'run_tests' tool. "
        "Analyze the results and provide a definitive summary. Your entire output will be passed to the team lead for review."
    ),
    expected_output="A string containing the complete test results: either the exact string 'ALL TESTS PASSED' or a detailed, multi-line failure log from pytest.",
    agent=unit_734_crew['tester'],
    tools=file_system_tools,
)

# -----------------------------------------------------------------------------
# DEBUGGING & REFINEMENT WORKFLOW (ENHANCED)
# -----------------------------------------------------------------------------

analyze_test_failure = Task(
    description=(
        "You are the team lead. A test has failed. Your task is to perform a root cause analysis and create a clear, actionable bug report.\n\n"
        "**CRITICAL ANALYSIS REQUIRED:**\n"
        "1.  **Review the Original Task:** First, carefully read the `Original Developer Task` to understand what the developer was *supposed* to build.\n"
        "2.  **Analyze the Failure Log:** Read the `Full Test Failure Log` to understand what went wrong. Was it an `AssertionError`, an `ImportError`, a `TypeError`, etc.?\n"
        "3.  **Perform Differential Diagnosis:** This is the most important step. You must decide the *true* root cause:\n"
        "    - **Case A: The Code is Buggy.** Does the failure log indicate that the code in `{file_name}` does not correctly implement the `Original Developer Task`? (e.g., a logic error, incorrect calculation).\n"
        "    - **Case B: The Test is Buggy.** Does the failure log indicate that the *test itself* in `{test_file_name}` is wrong? (e.g., it asserts for the wrong value, it tries to import a function with the wrong name, it has a syntax error).\n\n"
        "**FINAL OUTPUT FORMAT:**\n"
        "Your final output MUST be a single, valid JSON object with three keys:\n"
        "1.  `'analysis'`: A brief, one-sentence summary of your diagnosis.\n"
        "2.  `'file_to_fix'`: The string filename of the file that needs to be fixed (e.g., `{file_name}` or `{test_file_name}`).\n"
        "3.  `'next_task'`: A new, concise set of instructions for the responsible agent (either the developer or the tester) explaining exactly what needs to be fixed to make the test pass.\n"
        "---\n"
        "CONTEXT:\n\n"
        "Original Developer Task:\n'''\n{developer_task}\n'''\n\n"
        "Full Test Failure Log:\n'''\n{test_failure_log}\n'''\n"
    ),
    expected_output="A valid JSON object containing the keys 'analysis', 'file_to_fix', and 'next_task'.",
    agent=unit_734_crew['lead'],
)

# -----------------------------------------------------------------------------
# FINAL REPORTING WORKFLOW (ENHANCED)
# -----------------------------------------------------------------------------

compile_final_report = Task(
    description=(
        "Compile a final, client-facing report in Markdown format. The report must be professional and easy to understand.\n\n"
        "**CRITICAL**: It should include a friendly summary of the development process, referencing the initial brief, and a new section at the end titled '## Final Outcome'.\n"
        "Under '## Final Outcome', state the summary provided in '{final_outcome_summary}'.\n"
        "If the tests failed, include the complete, multi-line failure log from '{test_results}' inside a Python code block.\n\n"
        "Finally, present the final, verified Python code from '{file_name}' and the complete test suite from '{test_file_name}' in clean, readable Python code blocks.\n\n"
        "**CRITICAL FILE HANDLING:** If the content for `final_code` or `final_tests` is an error message (e.g., 'Error: Code could not be read...'), "
        "you MUST report that error in the final document instead of showing a code block. Do NOT invent code."
    ),
    expected_output="A comprehensive and accurate final report in Markdown format.",
    agent=unit_734_crew['liaison'],
)
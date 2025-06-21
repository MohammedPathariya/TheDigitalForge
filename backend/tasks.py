# backend/tasks.py
# CrewAI Task definitions & workflows for Unit 734 - The Digital Forge

from crewai import Task
from agents import unit_734_crew
from tools import file_system_tools

# -----------------------------------------------------------------------------
# DEFINE THE "HAPPY PATH" AND INITIAL SPRINT WORKFLOW
# -----------------------------------------------------------------------------

# Task 1: Client Liaison (Janus) - Create the initial brief
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

# Task 2: Team Lead (Athena) - Plan the development
define_development_plan = Task(
    description=(
        "Review the technical brief and deconstruct it into a clear, actionable development plan. "
        "Your final output must be a Python dictionary with two keys: 'developer_task' and 'tester_task'. "
        "The 'developer_task' should be a detailed, precise set of instructions for Hephaestus to write the code. "
        "The 'tester_task' should be a detailed, precise set of instructions for Argus to write the tests."
    ),
    expected_output="A Python dictionary with two keys: 'developer_task' and 'tester_task', containing detailed instructions.",
    agent=unit_734_crew['lead'],
    context=[create_technical_brief],
)

# Task 3: Developer (Hephaestus) - Write the code
generate_python_code = Task(
    description=(
        "Based on the provided development plan, write clean, efficient, and correct Python code. "
        "The code should be a single Python script. Use the 'save_file' tool to save the generated code to a file "
        "named 'product.py' inside the workspace."
    ),
    expected_output="The file path of the saved Python script: 'backend/workspace/product.py'.",
    agent=unit_734_crew['developer'],
    tools=file_system_tools,
    context=[define_development_plan],
)

# Task 4: Tester (Argus) - Write the tests
generate_test_suite = Task(
    description=(
        "Based on the provided testing plan and the generated Python code, create a comprehensive "
        "test suite using the pytest framework. The test suite must cover all core functionality "
        "and anticipated edge cases. Use the 'save_file' tool to save the tests to a file "
        "named 'test_product.py' inside the workspace."
    ),
    expected_output="The file path of the saved pytest test script: 'backend/workspace/test_product.py'.",
    agent=unit_734_crew['tester'],
    tools=file_system_tools,
    context=[generate_python_code, define_development_plan],
)

# Task 5: Tester (Argus) - Run the tests
execute_tests = Task(
    description=(
        "Execute the pytest test suite against the generated code using the 'run_tests' tool. "
        "The test file is located at 'backend/workspace/test_product.py'. "
        "Analyze the results and provide a definitive summary."
    ),
    expected_output="A string containing the test results: either 'ALL TESTS PASSED' or a detailed, multi-line failure log from pytest.",
    agent=unit_734_crew['tester'],
    tools=file_system_tools,
    context=[generate_test_suite],
)

# -----------------------------------------------------------------------------
# DEFINE THE "DEBUGGING" WORKFLOW
# -----------------------------------------------------------------------------

# Task 6: Team Lead (Athena) - Analyze failed tests
analyze_test_failure = Task(
    description=(
        "Analyze the detailed failure log from the test execution. Identify the root cause "
        "of the error and create a new, clear, and concise 'developer_task' that explains exactly "
        "what needs to be fixed. The original code and technical brief are available in the context."
    ),
    expected_output="A new developer_task as a string, precisely describing the bug and the required fix.",
    agent=unit_734_crew['lead'],
    context=[execute_tests, generate_python_code, create_technical_brief]
)

# Task 7: Developer (Hephaestus) - Fix the code
fix_python_code = Task(
    description=(
        "Review the bug report from the Team Lead and the original code. Implement the necessary changes to fix "
        "the bug. You must overwrite the original 'product.py' file with the corrected code using the "
        "'save_file' tool. Ensure the fix is robust and directly addresses the bug report."
    ),
    expected_output="The file path of the newly saved (corrected) Python script: 'backend/workspace/product.py'.",
    agent=unit_734_crew['developer'],
    tools=file_system_tools,
    context=[analyze_test_failure, generate_python_code]
)

# -----------------------------------------------------------------------------
# DEFINE THE "FINAL REPORT" WORKFLOW
# -----------------------------------------------------------------------------

# Task 8: Client Liaison (Janus) - Compile the final report
compile_final_report = Task(
    description=(
        "Compile a final, client-facing report in Markdown format. The report should include a friendly summary "
        "of the development process, noting any challenges and how they were overcome. It must include the "
        "final, verified Python code and the complete test suite that was used to validate it. "
        "Present the code and tests in clean, readable Python code blocks."
    ),
    expected_output="A comprehensive final report in Markdown format, including a summary, the final code, and the test suite.",
    agent=unit_734_crew['liaison'],
    context=[execute_tests, generate_python_code, generate_test_suite],
)

# Aggregate tasks for orchestration
all_tasks = [
    create_technical_brief,
    define_development_plan,
    generate_python_code,
    generate_test_suite,
    execute_tests,
    analyze_test_failure,
    fix_python_code,
    compile_final_report
]
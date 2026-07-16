"""Per-run CrewAI task construction."""

from collections.abc import Sequence
from dataclasses import dataclass

from crewai import Agent, Task
from crewai.tools import BaseTool


@dataclass(frozen=True)
class PipelineTasks:
    brief: Task
    plan: Task
    develop: Task
    test_suite: Task
    execute_tests: Task
    analyze_failure: Task
    final_report: Task


def build_tasks(
    agents: dict[str, Agent],
    file_system_tools: Sequence[BaseTool],
    retrieval_tools: Sequence[BaseTool] = (),
) -> PipelineTasks:
    """Create tasks bound to one run's agents and workspace tools."""
    brief = Task(
        description=(
            "Analyze the user's request and transform it into a structured technical brief. "
            "Ensure every part of the request is captured.\n\n"
            "User's Request:\n'''\n{user_request}\n'''\n\n"
            "Return Markdown with exactly these sections: 1. Project Overview, "
            "2. Core Objectives, 3. Key Features & Requirements, 4. Technical "
            "Constraints, and 5. Success Criteria. Derive content strictly from the "
            "request. Do not add or assume features, technologies, or constraints."
        ),
        expected_output="A complete Markdown technical brief faithful to the request.",
        agent=agents["liaison"],
    )
    plan = Task(
        description=(
            "Turn the technical brief into an actionable development plan that covers every "
            "requirement and success criterion.\n\nTechnical Brief:\n'''\n"
            "{technical_brief}\n'''\n\nReturn one valid JSON object with four keys: "
            "'file_name' for a PEP 8 Python filename, 'test_file_name' for its pytest "
            "suite, 'developer_task' with precise functions, inputs, outputs, and logic, "
            "and 'tester_task' with the test strategy and specific cases. When the brief "
            "depends on a third-party API, use search_official_documentation before "
            "finalizing API names or parameters."
        ),
        expected_output=(
            "A valid JSON object with file_name, test_file_name, developer_task, and "
            "tester_task."
        ),
        agent=agents["lead"],
        tools=list(retrieval_tools),
    )
    develop = Task(
        description=(
            "Implement the current instruction while preserving every original requirement. "
            "Do not add functionality or libraries that were not requested. If current code "
            "is present, repair that code and preserve unaffected behavior.\n\nOriginal "
            "Developer Task:\n'''\n{original_developer_task}\n'''\n\nCurrent "
            "Instruction:\n'''\n{developer_task}\n'''\n\nCurrent Code:\n'''\n"
            "{current_code}\n'''\n\nUse search_official_documentation before writing "
            "third-party API calls. Use save_file to save the code to {file_name}."
        ),
        expected_output="The saved Python file path.",
        agent=agents["developer"],
        tools=[*file_system_tools, *retrieval_tools],
    )
    test_suite = Task(
        description=(
            "Implement the current testing instruction while preserving the original test "
            "plan. Assertions must check exact expected outcomes. If current tests are "
            "present, repair only those tests and preserve unaffected coverage.\n\nOriginal "
            "Testing Plan:\n'''\n{original_tester_task}\n'''\n\nCurrent Testing "
            "Instruction:\n'''\n{tester_task}\n'''\n\nCurrent Tests:\n'''\n"
            "{current_tests}\n'''\n\nUse save_file to save it to {test_file_name}."
        ),
        expected_output="The saved pytest file path.",
        agent=agents["tester"],
        tools=list(file_system_tools),
    )
    execute_tests = Task(
        description=(
            "Run {test_file_name} against the generated code with run_tests. Return exactly "
            "'ALL TESTS PASSED' on success or the complete failure output."
        ),
        expected_output="ALL TESTS PASSED or a detailed pytest failure log.",
        agent=agents["tester"],
        tools=list(file_system_tools),
    )
    analyze_failure = Task(
        description=(
            "Use the sanitized failure class and evidence to identify the root cause. "
            "Candidate, timeout, and resource failures normally route to {file_name}; test "
            "failures normally route to {test_file_name}. Do not override that routing "
            "without evidence in the log. Return one valid JSON object with "
            "'analysis', 'file_to_fix', and 'next_task'. file_to_fix must be {file_name} or "
            "{test_file_name}.\n\nOriginal Developer Task:\n'''\n{developer_task}\n'''\n\n"
            "Current Application Code:\n'''\n{current_code}\n'''\n\nCurrent Test Code:\n'''\n"
            "{current_tests}\n'''\n\n"
            "Sanitized Test Failure Evidence:\n'''\n{test_failure_log}\n'''\n\nUse "
            "search_official_documentation when the root cause depends on third-party API "
            "behavior."
        ),
        expected_output="A valid JSON repair decision.",
        agent=agents["lead"],
        tools=list(retrieval_tools),
    )
    final_report = Task(
        description=(
            "Compile a client-facing Markdown report. Use the exact content in {final_code} "
            "and {final_tests}; do not generate or alter code. Include a process summary, a "
            "'## Final Outcome' section using {final_outcome_summary}, the complete failure "
            "log from {test_results} if tests failed, the code from {file_name}, and the tests "
            "from {test_file_name}.\n\nInitial Brief:\n'''\n{technical_brief}\n'''\n\n"
            "Final Code:\n'''\n{final_code}\n'''\n\nTests:\n'''\n{final_tests}\n'''"
            "\n\nRetrieved Documentation Sources:\n'''\n{retrieval_evidence}\n'''"
        ),
        expected_output="An accurate Markdown report using only the supplied context.",
        agent=agents["liaison"],
    )
    return PipelineTasks(
        brief=brief,
        plan=plan,
        develop=develop,
        test_suite=test_suite,
        execute_tests=execute_tests,
        analyze_failure=analyze_failure,
        final_report=final_report,
    )

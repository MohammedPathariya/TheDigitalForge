"""Per-run CrewAI task construction."""

from collections.abc import Sequence
from dataclasses import dataclass

from crewai import Agent, Task
from crewai.tools import BaseTool

from .models import DevelopmentPlan
from .sandbox_dependencies import SANDBOX_CAPABILITY_SUMMARY


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
            "requirement and success criterion. The original user request below is the "
            "immutable source of truth when it conflicts with the brief.\n\nOriginal User "
            "Request:\n'''\n{user_request}\n'''\n\nTechnical Brief:\n'''\n"
            "{technical_brief}\n'''\n\nReturn one valid JSON object with four keys: "
            "'file_name' for a PEP 8 Python filename, 'test_file_name' for its pytest "
            "suite, 'developer_task' as one JSON string with precise functions, inputs, "
            "outputs, and logic, and 'tester_task' as one JSON string describing exactly "
            "one representative happy-path case. The developer_task and tester_task must use the "
            "same exact public class and function names, file names, return keys, and main "
            "happy-path behavior from the brief. Do not rename a requested function or invent a different "
            "output schema. Do not add case-insensitive behavior or exact exception-message "
            "requirements unless the brief explicitly requires them. Do not return nested "
            "objects or arrays for developer_task or tester_task. Both tasks must be prose "
            "instructions, not example input and output data. developer_task must state the "
            "ordered implementation logic. tester_task must use ordinary valid inputs and "
            "verify only the main requested operation and expected output. Do not include "
            "malformed, missing, invalid, duplicate, boundary, ordering, mutation, exception, "
            "or type-subtlety cases in tester_task. "
            "When wording such as 'normalize' is ambiguous, choose the narrowest behavior "
            "directly supported by the brief and state it identically in both tasks. The "
            "offline sandbox provides "
            f"these pinned packages: {SANDBOX_CAPABILITY_SUMMARY}. Do not introduce an "
            "unrequested package. When the brief "
            "depends on a third-party API, use search_official_documentation before "
            "finalizing API names or parameters."
        ),
        expected_output=(
            "A valid JSON object with file_name, test_file_name, developer_task, and "
            "tester_task."
        ),
        agent=agents["lead"],
        tools=list(retrieval_tools),
        output_pydantic=DevelopmentPlan,
    )
    develop = Task(
        description=(
            "Implement the current instruction while preserving every original requirement. "
            "Do not add functionality or libraries that were not requested. If current code "
            "is present, repair that code and preserve unaffected behavior. The original user "
            "request is the immutable source of truth.\n\nOriginal User Request:\n'''\n"
            "{user_request}\n'''\n\nOriginal "
            "Developer Task:\n'''\n{original_developer_task}\n'''\n\nCurrent "
            "Instruction:\n'''\n{developer_task}\n'''\n\nCurrent Code:\n'''\n"
            "{current_code}\n'''\n\nUse the exact public class and function names, file name, return keys, and behavior "
            "required by the original developer task. During repair, inspect the current "
            "code for SyntaxError, indentation errors, missing symbols, and mismatches "
            "with the tester's expected import or return schema. Make the smallest fix and "
            "save only the application code to {file_name}. The offline sandbox provides "
            f"these pinned packages: {SANDBOX_CAPABILITY_SUMMARY}. Do not introduce an "
            "unrequested dependency. Use "
            "search_official_documentation before writing third-party API calls."
        ),
        expected_output="The saved Python file path.",
        agent=agents["developer"],
        tools=[*file_system_tools, *retrieval_tools],
    )
    test_suite = Task(
        description=(
            "Generate exactly one pytest test function covering one representative happy "
            "path with ordinary valid inputs. The test must verify only the main requested "
            "operation and its expected output. Do not generate malformed, missing, invalid, "
            "duplicate, boundary, ordering, mutation, exception, or type-subtlety cases. "
            "If current tests are present, replace them as needed so the suite still contains "
            "exactly one happy-path test. The original "
            "user request is the immutable source of truth.\n\nOriginal User Request:\n'''\n"
            "{user_request}\n'''\n\nOriginal "
            "Testing Plan:\n'''\n{original_tester_task}\n'''\n\nCurrent Testing "
            "Instruction:\n'''\n{tester_task}\n'''\n\nCurrent Tests:\n'''\n"
            "{current_tests}\n'''\n\nUse the exact application file name, public class and function names, return keys, and "
            "main happy-path behavior from the original testing plan. Import the requested "
            "symbol from the requested application module; never substitute a similar "
            "function name or invent a different output schema. Treat strings and identifiers "
            "as case-sensitive unless the original plan explicitly requires case-insensitive "
            "behavior. Do not assert an exact exception message unless its text is explicitly "
            "required. Do not invent normalization, response bodies, or validation rules "
            "that are absent from the original plan. During repair, remove or correct assertions that encode unstated "
            "requirements instead of preserving them. Before every save, audit every expected "
            "value and assertion against the original user request. Remove or correct any "
            "assertion that cannot be tied to an explicit requirement, even when the current "
            "repair instruction mentions a different defect. If the current tests say they "
            "were discarded, rebuild the suite from the original request instead of restoring "
            "prior assertions. Before saving, verify that the test file is complete, contains "
            "no Markdown fences, and is syntactically valid Python. "
            "The offline sandbox provides these pinned packages: "
            f"{SANDBOX_CAPABILITY_SUMMARY}. Do not import an unrequested dependency. Use "
            "save_file to save it to {test_file_name}."
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
            "Use the sanitized failure class and evidence to identify the root cause. The "
            "original user request is the immutable source of truth.\n\nOriginal User "
            "Request:\n'''\n{user_request}\n'''\n\n"
            "Candidate, timeout, and resource failures normally route to {file_name}; test "
            "failures normally route to {test_file_name}. Do not override that routing "
            "without evidence in the log. Return one valid JSON object with "
            "'analysis', 'file_to_fix', and 'next_task'. file_to_fix must be {file_name} or "
            "{test_file_name}.\n\nOriginal Developer Task:\n'''\n{developer_task}\n'''\n\n"
            "Current Application Code:\n'''\n{current_code}\n'''\n\nCurrent Test Code:\n'''\n"
            "{current_tests}\n'''\n\n"
            "Sanitized Test Failure Evidence:\n'''\n{test_failure_log}\n'''\n\nUse "
            "the traceback to distinguish application syntax or missing-symbol errors from "
            "a broken test import. If the application does not parse, repair the application "
            "first. If the application matches the original contract but the test imports "
            "a different symbol, asserts a different schema, assumes unstated case-insensitive "
            "behavior, or requires an unspecified exception message, repair the tests. For "
            "assertion failures, compare the actual candidate output and the test's expected "
            "output independently against the original request before routing. The generated "
            "testing plan is never allowed to override the original request. Use "
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

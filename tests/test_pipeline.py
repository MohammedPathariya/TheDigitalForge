from types import SimpleNamespace

import pytest

import backend.pipeline as pipeline_module
from backend.config import Settings
from backend.models import DevelopmentPlan, RunAgent, RunStage, RunState, RunStatus
from backend.pipeline import DevelopmentCrew


def test_complete_pipeline_instances_are_isolated() -> None:
    settings = Settings(openai_api_key="test-key")
    first = DevelopmentCrew("first request", settings)
    second = DevelopmentCrew("second request", settings)

    first.state.workspace.write("solution.py", "first")
    second.state.workspace.write("solution.py", "second")

    assert first.state.run_id != second.state.run_id
    assert first.state.workspace is not second.state.workspace
    assert first.state.workspace.read("solution.py") == "first"
    assert second.state.workspace.read("solution.py") == "second"
    assert first.agents["liaison"] is not second.agents["liaison"]
    assert first.tasks.develop is not second.tasks.develop
    assert all(agent.memory is None for agent in first.agents.values())
    assert all(agent.memory is None for agent in second.agents.values())
    assert all(agent.cache is False for agent in first.agents.values())
    assert all(agent.cache is False for agent in second.agents.values())


def test_run_state_tracks_workflow_lifecycle_and_outputs() -> None:
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    state = RunState(request="Build a solution")

    state.status = RunStatus.running
    state.stage = RunStage.testing
    state.attempts = 1
    state.technical_brief = "Brief"
    state.plan = plan
    state.test_results = "ALL TESTS PASSED"
    state.report = "Report"
    state.status = RunStatus.completed

    assert state.status is RunStatus.completed
    assert state.stage is RunStage.testing
    assert state.technical_brief == "Brief"
    assert state.plan == plan
    assert state.test_results == "ALL TESTS PASSED"
    assert state.report == "Report"


def test_pipeline_tracks_the_agent_currently_owning_the_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crew = DevelopmentCrew("build a solution", Settings(openai_api_key="test-key"))
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    observed_agents: list[RunAgent | None] = []

    monkeypatch.setattr(
        crew,
        "_run_developer",
        lambda _plan, _task: observed_agents.append(crew.state.active_agent),
    )
    monkeypatch.setattr(
        crew,
        "_run_test_author",
        lambda _plan, _task: observed_agents.append(crew.state.active_agent),
    )
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: "ALL TESTS PASSED")

    crew._develop_and_test(plan)

    assert observed_agents == [RunAgent.hephaestus, RunAgent.argus]


@pytest.mark.parametrize(
    ("file_name", "test_file_name"),
    [
        ("../solution.py", "test_solution.py"),
        ("Solution.py", "test_solution.py"),
        ("solution.py", "tests.py"),
        ("solution.py", "test_other.py"),
    ],
)
def test_development_plan_rejects_unsafe_or_mismatched_paths(
    file_name: str, test_file_name: str
) -> None:
    with pytest.raises(ValueError):
        DevelopmentPlan(
            file_name=file_name,
            test_file_name=test_file_name,
            developer_task="Implement the solution.",
            tester_task="Test the solution.",
        )


def test_development_plan_normalizes_structured_agent_instructions() -> None:
    plan = DevelopmentPlan.model_validate(
        {
            "file_name": "solution.py",
            "test_file_name": "test_solution.py",
            "developer_task": {
                "function": "solve",
                "steps": ["return the result"],
            },
            "tester_task": {"cases": ["empty input", "typical input"]},
        }
    )

    assert '"function": "solve"' in plan.developer_task
    assert '"cases"' in plan.tester_task


def test_self_healing_repairs_only_the_routed_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(openai_api_key="test-key", max_attempts=3)
    crew = DevelopmentCrew("build a solution", settings)
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    developer_tasks: list[str] = []
    tester_tasks: list[str] = []
    results = iter(
        [
            "TESTS FAILED:\nFAILURE CLASS: candidate",
            "ALL TESTS PASSED",
        ]
    )

    monkeypatch.setattr(
        crew,
        "_run_developer",
        lambda _plan, task: developer_tasks.append(task),
    )
    monkeypatch.setattr(
        crew,
        "_run_test_author",
        lambda _plan, task: tester_tasks.append(task),
    )
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: next(results))
    monkeypatch.setattr(
        crew,
        "_analyze_failure",
        lambda _plan, _result: {
            "file_to_fix": "solution.py",
            "next_task": "Repair the candidate.",
        },
    )

    result = crew._develop_and_test(plan)

    assert result == "ALL TESTS PASSED"
    assert developer_tasks == ["Implement the solution.", "Repair the candidate."]
    assert tester_tasks == ["Test the solution."]
    assert crew.state.attempts == 2
    assert [attempt.status.value for attempt in crew.state.attempt_history] == [
        "failed",
        "passed",
    ]


def test_self_healing_routes_test_repairs_without_rewriting_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(openai_api_key="test-key", max_attempts=3)
    crew = DevelopmentCrew("build a solution", settings)
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    developer_tasks: list[str] = []
    tester_tasks: list[str] = []
    results = iter(
        [
            "TESTS FAILED:\nFAILURE CLASS: test",
            "ALL TESTS PASSED",
        ]
    )

    monkeypatch.setattr(
        crew,
        "_run_developer",
        lambda _plan, task: developer_tasks.append(task),
    )
    monkeypatch.setattr(
        crew,
        "_run_test_author",
        lambda _plan, task: tester_tasks.append(task),
    )
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: next(results))
    monkeypatch.setattr(
        crew,
        "_analyze_failure",
        lambda _plan, _result: pytest.fail("test failures must route directly"),
    )

    result = crew._develop_and_test(plan)

    assert result == "ALL TESTS PASSED"
    assert developer_tasks == ["Implement the solution."]
    assert tester_tasks[0] == "Test the solution."
    assert "Repair only the current test suite" in tester_tasks[1]
    assert "FAILURE CLASS: test" in tester_tasks[1]
    assert crew.state.attempts == 2
    assert any(
        event.message == "The test suite is being repaired before the next attempt."
        for event in crew.state.events
    )


def test_timeout_routing_cannot_rewrite_tests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crew = DevelopmentCrew(
        "build a solution", Settings(openai_api_key="test-key", max_attempts=2)
    )
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    developer_tasks: list[str] = []
    tester_tasks: list[str] = []
    results = iter(["TESTS FAILED:\nFAILURE CLASS: timeout", "ALL TESTS PASSED"])

    monkeypatch.setattr(
        crew,
        "_run_developer",
        lambda _plan, task: developer_tasks.append(task),
    )
    monkeypatch.setattr(
        crew,
        "_run_test_author",
        lambda _plan, task: tester_tasks.append(task),
    )
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: next(results))
    monkeypatch.setattr(
        crew,
        "_analyze_failure",
        lambda _plan, _result: pytest.fail("timeouts must route directly"),
    )

    result = crew._develop_and_test(plan)

    assert result == "ALL TESTS PASSED"
    assert developer_tasks[0] == "Implement the solution."
    assert "Repair only the current application code" in developer_tasks[1]
    assert "FAILURE CLASS: timeout" in developer_tasks[1]
    assert tester_tasks == ["Test the solution."]


def test_request_contract_failure_routes_directly_to_developer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crew = DevelopmentCrew(
        "Implement `required_name(value)`.",
        Settings(openai_api_key="test-key", max_attempts=2),
    )
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    developer_tasks: list[str] = []
    results = iter(
        [
            "TESTS FAILED:\nFAILURE CLASS: candidate\n"
            "REQUEST CONTRACT FAILURE: required_name is missing",
            "ALL TESTS PASSED",
        ]
    )

    monkeypatch.setattr(
        crew,
        "_run_developer",
        lambda _plan, task: developer_tasks.append(task),
    )
    monkeypatch.setattr(crew, "_run_test_author", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: next(results))
    monkeypatch.setattr(
        crew,
        "_analyze_failure",
        lambda _plan, _result: pytest.fail("contract failures route directly"),
    )

    result = crew._develop_and_test(plan)

    assert result == "ALL TESTS PASSED"
    assert developer_tasks[0] == "Implement the solution."
    assert "REQUEST CONTRACT FAILURE" in developer_tasks[1]


def test_run_tests_preflight_rejects_missing_explicit_function(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crew = DevelopmentCrew(
        "Implement `required_name(value)`.", Settings(openai_api_key="test-key")
    )
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement required_name.",
        tester_task="Test required_name.",
    )
    crew.state.workspace.write("solution.py", "def wrong_name(value): return value\n")
    crew.state.workspace.write(
        "test_solution.py",
        "from solution import wrong_name\n\ndef test_value(): assert wrong_name(1) == 1\n",
    )
    monkeypatch.setattr(
        crew,
        "run_tests_tool",
        SimpleNamespace(
            run=lambda **_kwargs: pytest.fail(
                "invalid artifacts must not reach the sandbox"
            )
        ),
    )

    result = crew._run_tests(plan)

    assert "FAILURE CLASS: candidate" in result
    assert "required_name" in result


def test_run_tests_preflight_rejects_test_without_application_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crew = DevelopmentCrew(
        "Implement `required_name(value)`.", Settings(openai_api_key="test-key")
    )
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement required_name.",
        tester_task="Test required_name.",
    )
    crew.state.workspace.write(
        "solution.py", "def required_name(value): return value\n"
    )
    crew.state.workspace.write(
        "test_solution.py",
        "def required_name(value): return value\n\n"
        "def test_value(): assert required_name(1) == 1\n",
    )
    monkeypatch.setattr(
        crew,
        "run_tests_tool",
        SimpleNamespace(
            run=lambda **_kwargs: pytest.fail(
                "invalid artifacts must not reach the sandbox"
            )
        ),
    )

    result = crew._run_tests(plan)

    assert "FAILURE CLASS: test" in result
    assert "must import the application module" in result


def test_repair_crews_receive_original_artifacts_and_requirements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_inputs: list[dict[str, object]] = []

    class CapturingCrew:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def kickoff(self, *, inputs: dict[str, object]) -> str:
            captured_inputs.append(inputs)
            if "test_failure_log" in inputs:
                return (
                    '{"analysis":"candidate bug","file_to_fix":"solution.py",'
                    '"next_task":"repair it"}'
                )
            return "saved"

    monkeypatch.setattr(pipeline_module, "Crew", CapturingCrew)
    crew = DevelopmentCrew("build a solution", Settings(openai_api_key="test-key"))
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    crew.state.workspace.write("solution.py", "def answer(): return 1\n")
    crew.state.workspace.write(
        "test_solution.py", "def test_answer(): assert answer() == 2\n"
    )

    crew._run_developer(plan, "Repair the return value.")
    crew._run_test_author(plan, "Repair the assertion.")
    crew._analyze_failure(plan, "TESTS FAILED")

    assert captured_inputs[0]["original_developer_task"] == plan.developer_task
    assert captured_inputs[0]["user_request"] == "build a solution"
    assert captured_inputs[0]["current_code"] == "def answer(): return 1\n"
    assert captured_inputs[1]["original_tester_task"] == plan.tester_task
    assert captured_inputs[1]["user_request"] == "build a solution"
    assert "assert answer() == 2" in str(captured_inputs[1]["current_tests"])
    assert captured_inputs[2]["current_code"] == "def answer(): return 1\n"
    assert captured_inputs[2]["user_request"] == "build a solution"
    assert "assert answer() == 2" in str(captured_inputs[2]["current_tests"])


def test_self_healing_stops_after_three_candidate_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(openai_api_key="test-key", max_attempts=3)
    crew = DevelopmentCrew("build a solution", settings)
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    failure = "TESTS FAILED:\nFAILURE CLASS: candidate"
    repairs = 0

    def analyze_failure(_plan: DevelopmentPlan, _result: str) -> dict[str, object]:
        nonlocal repairs
        repairs += 1
        return {
            "file_to_fix": "solution.py",
            "next_task": f"Repair candidate {repairs}.",
        }

    monkeypatch.setattr(crew, "_run_developer", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_test_author", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: failure)
    monkeypatch.setattr(crew, "_analyze_failure", analyze_failure)

    result = crew._develop_and_test(plan)

    assert result == failure
    assert crew.state.attempts == 3
    assert repairs == 2


def test_infrastructure_retries_do_not_consume_candidate_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(openai_api_key="test-key", max_attempts=3)
    crew = DevelopmentCrew("build a solution", settings)
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    executions = iter(
        [
            "TESTS FAILED:\nFAILURE CLASS: infrastructure",
            "ALL TESTS PASSED",
        ]
    )

    monkeypatch.setattr(crew, "_run_developer", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_test_author", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: next(executions))

    result = crew._develop_and_test(plan)

    assert result == "ALL TESTS PASSED"
    assert crew.state.attempts == 1


def test_repeated_infrastructure_failures_stop_without_consuming_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(openai_api_key="test-key", max_attempts=3)
    crew = DevelopmentCrew("build a solution", settings)
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    infrastructure_failure = "TESTS FAILED:\nFAILURE CLASS: infrastructure"

    monkeypatch.setattr(crew, "_run_developer", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_test_author", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_tests", lambda _plan: infrastructure_failure)

    result = crew._develop_and_test(plan)

    assert "INFRASTRUCTURE RETRIES EXHAUSTED" in result
    assert crew.state.attempts == 0


def test_non_retryable_infrastructure_failure_stops_after_one_test_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crew = DevelopmentCrew(
        "build a solution", Settings(openai_api_key="test-key", max_attempts=3)
    )
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    executions = 0

    def missing_dependency(_plan: DevelopmentPlan) -> str:
        nonlocal executions
        executions += 1
        return "TESTS FAILED:\nFAILURE CLASS: infrastructure\nRETRYABLE: no"

    monkeypatch.setattr(crew, "_run_developer", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_test_author", lambda _plan, _task: None)
    monkeypatch.setattr(crew, "_run_tests", missing_dependency)

    result = crew._develop_and_test(plan)

    assert "SANDBOX CONFIGURATION FAILURE" in result
    assert executions == 1
    assert crew.state.attempts == 0
    assert len(crew.state.attempt_history) == 1


def test_run_reports_infrastructure_exhaustion_separately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crew = DevelopmentCrew("build a solution", Settings(openai_api_key="test-key"))
    infrastructure_failure = (
        "TESTS FAILED:\n"
        "FAILURE CLASS: infrastructure\n"
        "INFRASTRUCTURE RETRIES EXHAUSTED: candidate attempt was not consumed."
    )

    class StubCrew:
        calls = 0

        def __init__(self, **_kwargs: object) -> None:
            pass

        def kickoff(self, *, inputs: dict[str, object]) -> str:
            StubCrew.calls += 1
            if StubCrew.calls == 1:
                return "Brief"
            return (
                '{"file_name":"solution.py",'
                '"test_file_name":"test_solution.py",'
                '"developer_task":"Implement it.",'
                '"tester_task":"Test it."}'
            )

    monkeypatch.setattr(pipeline_module, "Crew", StubCrew)
    monkeypatch.setattr(crew, "_develop_and_test", lambda _plan: infrastructure_failure)
    monkeypatch.setattr(crew, "_generate_final_report", lambda *_args: "Report")

    result = crew.run()

    assert result.status is RunStatus.failed
    assert crew.state.attempts == 0
    assert crew.state.events[-1].message == (
        "The run stopped after repeated sandbox infrastructure failures."
    )

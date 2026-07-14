from backend.config import Settings
from backend.models import DevelopmentPlan, RunState, RunStatus
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


def test_run_state_tracks_workflow_lifecycle_and_outputs() -> None:
    plan = DevelopmentPlan(
        file_name="solution.py",
        test_file_name="test_solution.py",
        developer_task="Implement the solution.",
        tester_task="Test the solution.",
    )
    state = RunState(request="Build a solution")

    state.status = RunStatus.running
    state.attempts = 1
    state.technical_brief = "Brief"
    state.plan = plan
    state.test_results = "ALL TESTS PASSED"
    state.report = "Report"
    state.status = RunStatus.completed

    assert state.status is RunStatus.completed
    assert state.technical_brief == "Brief"
    assert state.plan == plan
    assert state.test_results == "ALL TESTS PASSED"
    assert state.report == "Report"

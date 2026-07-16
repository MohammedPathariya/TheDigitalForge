from backend.agents import build_agents
from backend.models import RunState
from backend.retrieval import build_retrieval_tools
from backend.tasks import build_tasks
from rag.index import ChromaRetriever
from rag.models import RetrievalEvent


def test_retrieval_tool_logs_cited_sources_per_run() -> None:
    events: list[RetrievalEvent] = []
    tool = build_retrieval_tools(ChromaRetriever(), events, result_limit=2)[0]

    output = tool.run(query="How does FastAPI response_model filter output?")

    assert len(events) == 1
    assert events[0].query == "How does FastAPI response_model filter output?"
    assert events[0].results
    assert "fastapi-models-0-139-0" in output
    assert "https://fastapi.tiangolo.com/" in output
    assert "content" not in events[0].model_dump()["results"][0]


def test_only_lead_and_developer_tasks_receive_retrieval_tool() -> None:
    retrieval_tool = build_retrieval_tools(ChromaRetriever(), [])[0]
    tasks = build_tasks(build_agents(), [], [retrieval_tool])

    assert [tool.name for tool in tasks.plan.tools or []] == [
        "search_official_documentation"
    ]
    assert [tool.name for tool in tasks.develop.tools or []] == [
        "search_official_documentation"
    ]
    assert [tool.name for tool in tasks.analyze_failure.tools or []] == [
        "search_official_documentation"
    ]
    assert tasks.brief.tools == []
    assert tasks.test_suite.tools == []
    assert tasks.execute_tests.tools == []
    assert tasks.final_report.tools == []


def test_retrieval_events_are_isolated_between_runs() -> None:
    first = RunState(request="first")
    second = RunState(request="second")
    tool = build_retrieval_tools(ChromaRetriever(), first.retrieval_events)[0]

    tool.run(query="OpenAI Responses API store false")

    assert len(first.retrieval_events) == 1
    assert second.retrieval_events == []

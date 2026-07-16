from benchmark.catalog import BENCHMARK_VERSION, load_tasks
from benchmark.hidden_cases import HIDDEN_CASES, evaluator_sha256
from benchmark.models import Difficulty


def test_catalog_has_versioned_balanced_task_set() -> None:
    tasks = load_tasks()

    assert BENCHMARK_VERSION == "1.1.0"
    assert len(tasks) == 20
    assert len({task.id for task in tasks}) == 20
    assert sum(task.difficulty is Difficulty.easy for task in tasks) == 10
    assert sum(task.difficulty is Difficulty.medium for task in tasks) == 10
    assert all(task.version == BENCHMARK_VERSION for task in tasks)


def test_every_task_has_hidden_cases_and_stable_evaluator_digest() -> None:
    task_ids = {task.id for task in load_tasks()}

    assert set(HIDDEN_CASES) == task_ids
    assert all(len(cases) >= 4 for cases in HIDDEN_CASES.values())
    assert len(evaluator_sha256()) == 64
    assert evaluator_sha256() == evaluator_sha256()


def test_hidden_case_collections_are_immutable() -> None:
    cases = HIDDEN_CASES["forge_easy_01"]

    assert isinstance(cases, tuple)
    assert isinstance(cases[0].args, tuple)
    assert isinstance(cases[0].args[0], tuple)

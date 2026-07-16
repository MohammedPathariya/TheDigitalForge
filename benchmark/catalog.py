"""Load and validate the public, versioned benchmark catalog."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import TypeAdapter

from .models import BenchmarkTask

BENCHMARK_VERSION = "1.1.0"
CATALOG_PATH = Path(__file__).parent / "tasks" / "v1.json"


@lru_cache
def load_tasks() -> tuple[BenchmarkTask, ...]:
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    tasks = TypeAdapter(tuple[BenchmarkTask, ...]).validate_python(raw)
    ids = [task.id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Benchmark task IDs must be unique.")
    return tasks


def get_task(task_id: str) -> BenchmarkTask:
    for task in load_tasks():
        if task.id == task_id:
            return task
    raise KeyError(f"Unknown benchmark task: {task_id}")

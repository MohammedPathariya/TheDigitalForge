"""Load immutable benchmark reports for the frontend dashboard."""

from pathlib import Path

from benchmark.models import BenchmarkReport


def load_benchmark_reports(root: Path) -> tuple[BenchmarkReport, ...]:
    if not root.exists():
        return ()
    reports = [
        BenchmarkReport.model_validate_json(path.read_text(encoding="utf-8"))
        for path in root.glob("*/report.json")
    ]
    return tuple(sorted(reports, key=lambda report: report.completed_at, reverse=True))

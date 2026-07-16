"""Load immutable benchmark reports for the frontend dashboard."""

from pathlib import Path

from benchmark.catalog import BENCHMARK_VERSION
from benchmark.models import BenchmarkReport


def load_benchmark_reports(root: Path) -> tuple[BenchmarkReport, ...]:
    if not root.exists():
        return ()
    reports = [
        report
        for path in root.glob("*/report.json")
        if (
            report := BenchmarkReport.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        ).benchmark_version
        == BENCHMARK_VERSION
    ]
    return tuple(sorted(reports, key=lambda report: report.completed_at, reverse=True))

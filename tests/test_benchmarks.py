from pathlib import Path

from backend.benchmarks import load_benchmark_reports
from benchmark.catalog import BENCHMARK_VERSION
from benchmark.models import BenchmarkReport, utc_now


def _write_report(root: Path, run_id: str, benchmark_version: str) -> None:
    report = BenchmarkReport(
        benchmark_version=benchmark_version,
        evaluator_sha256="0" * 64,
        run_id=run_id,
        model="test-model",
        sandbox_backend="stub",
        started_at=utc_now(),
        completed_at=utc_now(),
        tasks_passed=0,
        tasks_total=0,
        results=(),
    )
    report.write(root / run_id / "report.json")


def test_load_benchmark_reports_filters_obsolete_versions(tmp_path: Path) -> None:
    _write_report(tmp_path, "old-run", "1.0.0")
    _write_report(tmp_path, "current-run", BENCHMARK_VERSION)

    reports = load_benchmark_reports(tmp_path)

    assert [report.run_id for report in reports] == ["current-run"]

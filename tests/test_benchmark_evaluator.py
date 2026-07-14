from pathlib import Path

from benchmark.catalog import get_task
from benchmark.evaluator import evaluate_candidate


def test_evaluator_accepts_correct_candidate(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "def dedupe_crates(crate_ids):\n    return list(dict.fromkeys(crate_ids))\n",
        encoding="utf-8",
    )

    result = evaluate_candidate(get_task("forge_easy_02"), candidate)

    assert result.passed is True
    assert result.tests_passed == result.tests_total


def test_evaluator_reports_hidden_failure_without_revealing_all_cases(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "def dedupe_crates(crate_ids):\n    return []\n", encoding="utf-8"
    )

    result = evaluate_candidate(get_task("forge_easy_02"), candidate)

    assert result.passed is False
    assert result.tests_passed < result.tests_total
    assert result.error is not None
    assert result.error.startswith("hidden case ")
    assert "expected" not in result.error


def test_evaluator_sanitizes_candidate_exceptions(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "def dedupe_crates(crate_ids):\n    raise ValueError(crate_ids)\n",
        encoding="utf-8",
    )

    result = evaluate_candidate(get_task("forge_easy_02"), candidate)

    assert result.error == "candidate raised ValueError during hidden case 0"
    assert "same" not in result.error


def test_correct_palindrome_candidate_passes_all_hidden_cases(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "def is_mirrored_inscription(text):\n"
        "    value = ''.join(\n"
        "        char.lower() for char in text\n"
        "        if char.isascii() and char.isalnum()\n"
        "    )\n"
        "    return value == value[::-1]\n",
        encoding="utf-8",
    )

    result = evaluate_candidate(get_task("forge_easy_09"), candidate)

    assert result.passed is True


def test_correct_budget_pair_candidate_passes_all_hidden_cases(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "def nearest_budget_pair(costs, budget):\n"
        "    ranked = (\n"
        "        (abs(costs[i] + costs[j] - budget), i, j)\n"
        "        for i in range(len(costs))\n"
        "        for j in range(i + 1, len(costs))\n"
        "    )\n"
        "    return list(min(ranked)[1:])\n",
        encoding="utf-8",
    )

    result = evaluate_candidate(get_task("forge_medium_09"), candidate)

    assert result.passed is True

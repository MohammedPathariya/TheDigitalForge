from backend.artifact_validation import (
    explicit_function_names,
    normalize_test_imports,
    validate_application_artifact,
    validate_test_artifact,
)


def test_extracts_explicit_function_names_without_duplicates() -> None:
    request = "Implement `load_items(lines)` and test `load_items([])`."

    assert explicit_function_names(request) == ("load_items",)


def test_application_validation_rejects_contract_drift() -> None:
    error = validate_application_artifact(
        "Implement `load_inventory_deltas(lines)`.",
        "def process_inventory(lines):\n    return {}\n",
    )

    assert error == (
        "application is missing explicit public function(s): load_inventory_deltas"
    )


def test_application_validation_rejects_invalid_python() -> None:
    error = validate_application_artifact(
        "Implement `route_ticket(ticket)`.",
        "def route_ticket(ticket):\n    return 'support'}\n",
    )

    assert error is not None
    assert "invalid Python syntax" in error


def test_test_validation_requires_real_application_import() -> None:
    error = validate_test_artifact(
        "solution.py",
        "Implement `solve(value)`.",
        "def solve(value):\n    return value\n\ndef test_solve():\n    assert solve(1) == 1\n",
    )

    assert error == "test suite must import the application module 'solution'"


def test_test_validation_accepts_matching_import() -> None:
    error = validate_test_artifact(
        "solution.py",
        "Implement `solve(value)`.",
        "from solution import solve\n\ndef test_solve():\n    assert solve(1) == 1\n",
    )

    assert error is None


def test_normalizes_explicit_function_import_to_application_module() -> None:
    test_code = (
        "import pytest\n"
        "from your_module import solve\n\n"
        "def test_solve():\n"
        "    assert solve(1) == 1\n"
    )

    normalized = normalize_test_imports(
        "solution.py", "Implement `solve(value)`.", test_code
    )

    assert normalized == test_code.replace("from your_module", "from solution")

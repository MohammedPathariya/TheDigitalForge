"""Deterministic validation for model-generated Python artifacts."""

import ast
import re
from pathlib import Path

_EXPLICIT_FUNCTION_PATTERN = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_FROM_IMPORT_PATTERN = re.compile(
    r"(?P<prefix>\bfrom\s+)(?P<module>[A-Za-z_][A-Za-z0-9_.]*)(?P<suffix>\s+import\b)"
)


def explicit_function_names(user_request: str) -> tuple[str, ...]:
    """Return explicitly named backtick-delimited functions in request order."""
    return tuple(dict.fromkeys(_EXPLICIT_FUNCTION_PATTERN.findall(user_request)))


def validate_application_artifact(user_request: str, code: str) -> str | None:
    """Validate syntax and explicit top-level function contracts."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        location = f"line {exc.lineno}" if exc.lineno else "unknown line"
        return f"application has invalid Python syntax at {location}: {exc.msg}"

    required = explicit_function_names(user_request)
    if not required:
        return None
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = [name for name in required if name not in defined]
    if missing:
        return "application is missing explicit public function(s): " + ", ".join(
            missing
        )
    return None


def normalize_test_imports(
    application_file: str, user_request: str, test_code: str
) -> str:
    """Point explicit function imports at the planned application module."""
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return test_code

    required = set(explicit_function_names(user_request))
    if not required:
        return test_code

    application_module = Path(application_file).stem
    lines = test_code.splitlines(keepends=True)
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.module == application_module:
            continue
        if not any(alias.name in required for alias in node.names):
            continue

        line_index = node.lineno - 1
        line = lines[line_index]
        match = _FROM_IMPORT_PATTERN.search(line, node.col_offset)
        if match is None:
            continue
        lines[line_index] = (
            line[: match.start("module")]
            + application_module
            + line[match.end("module") :]
        )
    return "".join(lines)


def validate_test_artifact(
    application_file: str, user_request: str, test_code: str
) -> str | None:
    """Validate test syntax, application imports, and contract ownership."""
    try:
        tree = ast.parse(test_code)
    except SyntaxError as exc:
        location = f"line {exc.lineno}" if exc.lineno else "unknown line"
        return f"test suite has invalid Python syntax at {location}: {exc.msg}"

    application_module = Path(application_file).stem
    imports_application = any(
        (isinstance(node, ast.ImportFrom) and node.module == application_module)
        or (
            isinstance(node, ast.Import)
            and any(alias.name == application_module for alias in node.names)
        )
        for node in tree.body
    )
    if not imports_application:
        return f"test suite must import the application module {application_module!r}"

    required = set(explicit_function_names(user_request))
    redefined = sorted(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in required
    )
    if redefined:
        return "test suite redefines application function(s): " + ", ".join(redefined)
    return None

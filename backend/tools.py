# backend/tools.py
# @tool-decorated functions for Unit 734 to interact with the filesystem.

import subprocess
import sys
from pathlib import Path

# Attempt to import the correct decorator
try:
    from crewai_tools import tool
except ImportError:
    from crewai.tools import tool

# --- Configuration: Define the AI's workspace for security ---
WORKSPACE_DIR = Path('backend/workspace')
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the workspace exists

def _is_path_in_workspace(path: Path) -> bool:
    """Checks if the given path is securely within the workspace."""
    absolute_path = path.resolve()
    workspace_path = WORKSPACE_DIR.resolve()
    return workspace_path in absolute_path.parents or absolute_path == workspace_path

# ----------------------------------------
# Tool 1: save_file
# ----------------------------------------
@tool
def save_file(file_path: str, content: str) -> str:
    """
    Saves the given content to a specified file within the workspace.

    Args:
        file_path: Relative path inside the workspace (e.g., 'product.py', 'tests/test_logic.py').
        content: The content to write to the file.

    Returns:
        Confirmation message or an error string.
    """
    path = WORKSPACE_DIR / file_path
    if not _is_path_in_workspace(path):
        return "Error: Path is outside the designated workspace. Operation denied."
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File saved successfully to: {path.resolve()}"
    except Exception as e:
        return f"Error saving file: {e}"

# ----------------------------------------
# Tool 2: run_tests
# ----------------------------------------
@tool
def run_tests(test_file_path: str) -> str:
    """
    Executes a pytest test suite on a given file within the workspace.

    Args:
        test_file_path: Relative path to the test file (e.g., 'test_product.py').

    Returns:
        'ALL TESTS PASSED' or a detailed failure log.
    """
    path = WORKSPACE_DIR / test_file_path
    if not _is_path_in_workspace(path):
        return "Error: Cannot run tests on a file outside the designated workspace."
    if not path.is_file():
        return f"Error: Test file not found at {path.resolve()}"

    cmd = [
        sys.executable, "-m", "pytest",
        str(path.resolve()),
        "--maxfail=1",
        "--disable-warnings",
        "-q"
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=WORKSPACE_DIR
        )
        return "ALL TESTS PASSED"
    except subprocess.CalledProcessError as e:
        return (
            f"TESTS FAILED:\n--- STDOUT ---\n{e.stdout}\n"
            f"--- STDERR ---\n{e.stderr}"
        ).strip()
    except Exception as e:
        return f"An unexpected error occurred while running tests: {e}"

# Export the tools list
file_system_tools = [save_file, run_tests]
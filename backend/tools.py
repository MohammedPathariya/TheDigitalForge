# backend/tools.py
# @tool-decorated functions for Unit 734 to interact with the filesystem.

import os
import subprocess
import sys # <-- Import the sys module
from pathlib import Path

# --- FIX for ImportError ---
try:
    from crewai_tools import tool
except ImportError:
    from crewai.tools import tool


# --- Configuration: Define the AI's workspace for security ---
WORKSPACE_DIR = Path('backend/workspace')
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True) # Ensure the workspace exists

def _is_path_in_workspace(path: Path) -> bool:
    """Checks if the given path is securely within the workspace."""
    absolute_path = path.resolve()
    return WORKSPACE_DIR.resolve() in absolute_path.parents or \
           absolute_path == WORKSPACE_DIR.resolve()

# ----------------------------------------
# Tool 1: Save File
# ----------------------------------------
@tool
def save_file(file_path: str, content: str) -> str:
    """
    Saves the given content to a specified file.

    Args:
        file_path (str): The relative path to the file within the workspace.
                         e.g., 'product.py' or 'tests/test_logic.py'
        content (str): The string content to write to the file.

    Returns:
        str: A confirmation message indicating the absolute path of the saved file.
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
# Tool 2: Run Pytest Tests
# ----------------------------------------
@tool
def run_tests(test_file_path: str) -> str:
    """
    Executes a pytest test suite on a given file within the workspace.

    Args:
        test_file_path (str): The relative path to the test file inside the workspace.
                              e.g., 'test_product.py'

    Returns:
        str: 'ALL TESTS PASSED' if successful, otherwise the detailed pytest
             error log for debugging.
    """
    path = WORKSPACE_DIR / test_file_path

    if not _is_path_in_workspace(path):
        return "Error: Cannot run tests on a file outside the designated workspace."

    if not path.is_file():
        return f"Error: Test file not found at {path.resolve()}"

    # --- FIX: Use sys.executable to run pytest as a module ---
    # This ensures we use the pytest from the correct virtual environment.
    command = [
        sys.executable,     # The path to the current python interpreter
        "-m", "pytest",     # Run pytest as a module
        str(path.resolve()), 
        "--maxfail=1",      # Stop after the first failure
        "--disable-warnings",
        "-q"                # Quiet mode for cleaner output
    ]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=WORKSPACE_DIR # Run pytest from the workspace directory
        )
        return "ALL TESTS PASSED"
    except subprocess.CalledProcessError as e:
        failure_log = f"TESTS FAILED:\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}"
        return failure_log.strip()
    except Exception as e:
        return f"An unexpected error occurred while running tests: {e}"


# --- Export the list of tools for the agents to use ---
file_system_tools = [save_file, run_tests]
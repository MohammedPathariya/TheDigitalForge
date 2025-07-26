# backend/tools.py

"""
Tool definitions for an in-memory workspace. This approach avoids writing
to a persistent disk, making it suitable for serverless and containerized
deployment environments like Render.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from crewai_tools import tool
except ImportError:
    from crewai.tools import tool

# --- In-Memory Workspace ---
# A simple dictionary to act as our virtual file system.
IN_MEMORY_WORKSPACE = {}

def clear_workspace():
    """Clears the in-memory workspace. Called before each new run."""
    global IN_MEMORY_WORKSPACE
    IN_MEMORY_WORKSPACE.clear()
    print("--- In-memory workspace cleared. ---")


@tool
def save_file(file_path: str, content: str) -> str:
    """
    Saves content to a specified file path in the in-memory workspace.
    This does NOT write to the physical disk.
    """
    global IN_MEMORY_WORKSPACE
    # Use Path to normalize the path and remove any leading slashes
    normalized_path = str(Path(file_path))
    IN_MEMORY_WORKSPACE[normalized_path] = content
    return f"File '{normalized_path}' saved in memory."

@tool
def run_tests(test_file_path: str) -> str:
    """
    Executes a pytest suite by writing the necessary files to temporary
    locations on disk, running the tests, and then cleaning up.
    """
    global IN_MEMORY_WORKSPACE
    
    # Normalize paths for lookup
    normalized_test_path = str(Path(test_file_path))
    
    # Infer the main code file path from the test file path
    if not normalized_test_path.startswith("test_"):
        return "Error: Test file name must start with 'test_'."
    code_file_path = normalized_test_path.replace("test_", "", 1)

    # Retrieve file contents from memory
    code_content = IN_MEMORY_WORKSPACE.get(code_file_path)
    test_content = IN_MEMORY_WORKSPACE.get(normalized_test_path)

    if code_content is None:
        return f"Error: Code file '{code_file_path}' not found in memory."
    if test_content is None:
        return f"Error: Test file '{normalized_test_path}' not found in memory."

    # Use a temporary directory to safely write files for the test run
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create temporary file paths
        temp_code_file = temp_dir_path / code_file_path
        temp_test_file = temp_dir_path / normalized_test_path
        
        # Write the in-memory content to the temporary files
        temp_code_file.write_text(code_content, encoding='utf-8')
        temp_test_file.write_text(test_content, encoding='utf-8')

        # Command to execute pytest
        cmd = [
            sys.executable, "-m", "pytest",
            str(temp_test_file),
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
                cwd=temp_dir_path # Run pytest from within the temp directory
            )
            return "ALL TESTS PASSED"
        except subprocess.CalledProcessError as e:
            return (
                f"TESTS FAILED:\n--- STDOUT ---\n{e.stdout}\n"
                f"--- STDERR ---\n{e.stderr}"
            ).strip()
        except Exception as e:
            return f"An unexpected error occurred while running tests: {e}"

# The only tools needed are save_file and run_tests.
# save_report is no longer needed as the report is generated and returned directly.
file_system_tools = [save_file, run_tests]
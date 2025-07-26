# backend/tools.py

"""
Tool definitions for file I/O, test execution, and reporting
in the Digital Forge pipeline. Each function is exposed as
a CrewAI tool and therefore must have its own docstring.
"""

import subprocess
import sys
from pathlib import Path
import markdown

# --- Robust Tool Import ---
# Try the new package first; fall back to the built-in one.
try:
    from crewai_tools import tool
except ImportError:
    from crewai.tools import tool

# --- Configuration: Define the AI's workspace for security ---
WORKSPACE_DIR = Path('backend/workspace')
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

def _is_path_in_workspace(path: Path) -> bool:
    """
    Determine whether the given path is inside our secure workspace directory.
    """
    absolute_path = path.resolve()
    workspace_path = WORKSPACE_DIR.resolve()
    return workspace_path in absolute_path.parents or absolute_path == workspace_path

@tool
def save_file(file_path: str, content: str) -> str:
    """
    Saves the given content to a specified file within the workspace.
    Returns a success message or an error if the path is invalid or write fails.
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

@tool
def run_tests(test_file_path: str) -> str:
    """
    Executes a pytest suite on the given test file inside the workspace.
    Returns 'ALL TESTS PASSED' or a detailed failure log.
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

@tool
def save_report(file_name_stem: str, markdown_content: str) -> str:
    """
    Saves a markdown report as both .md and styled .html in the workspace.
    Returns success paths or an error message on failure.
    """
    base_name = Path(file_name_stem).stem
    md_path = WORKSPACE_DIR / f"{base_name}.md"
    html_path = WORKSPACE_DIR / f"{base_name}.html"

    if not _is_path_in_workspace(md_path) or not _is_path_in_workspace(html_path):
        return "Error: Path is outside the designated workspace. Operation denied."

    try:
        # Save raw Markdown
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Convert to HTML
        html_body = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
            <title>{base_name.replace('_',' ').title()}</title>
            <style>
                body {{ font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; line-height:1.6; padding:20px; max-width:900px; margin:20px auto; background:#f9f9f9; color:#333; }}
                pre {{ background:#2c3e50; color:#ecf0f1; padding:15px; border-radius:8px; overflow-x:auto; }}
                code {{ font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,Courier,monospace; }}
                h1,h2,h3,h4,h5,h6 {{ color:#2c3e50; border-bottom:2px solid #ecf0f1; padding-bottom:10px; }}
                table {{ border-collapse:collapse; width:100%; box-shadow:0 2px 3px rgba(0,0,0,0.1); }}
                th,td {{ border:1px solid #ddd; padding:12px; text-align:left; }}
                th {{ background-color:#3498db; color:white; }}
                tr:nth-child(even) {{ background-color:#f2f2f2; }}
                blockquote {{ background:#ecf0f1; border-left:5px solid #3498db; margin:20px 0; padding:15px; }}
            </style>
        </head>
        <body>{html_body}</body>
        </html>
        """

        # Write HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return (
            f"Report saved as Markdown to: {md_path.resolve()} and HTML to: {html_path.resolve()}"
        )
    except Exception as e:
        return f"Error saving report: {e}"

# Export the tools list for use by the pipeline
file_system_tools = [save_file, run_tests, save_report]
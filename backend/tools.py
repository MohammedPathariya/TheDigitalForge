# backend/tools.py

import subprocess, sys
from pathlib import Path
import markdown

try:
    from crewai_tools import tool
except ImportError:
    from crewai.tools import tool

WORKSPACE_DIR = Path('backend/workspace')
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

def _is_path_in_workspace(p: Path) -> bool:
    return WORKSPACE_DIR.resolve() in p.resolve().parents or p.resolve() == WORKSPACE_DIR.resolve()

@tool
def save_file(file_path: str, content: str) -> str:
    path = WORKSPACE_DIR / file_path
    if not _is_path_in_workspace(path):
        return "Error: Path outside workspace."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return f"File saved to {file_path}"

@tool
def run_tests(test_file_path: str) -> str:
    path = WORKSPACE_DIR / test_file_path
    if not path.is_file():
        return f"Error: Test file not found: {test_file_path}"
    cmd = [sys.executable, "-m", "pytest", str(path.resolve()), "--maxfail=1", "-q"]
    try:
        subprocess.run(cmd, cwd=WORKSPACE_DIR, check=True, capture_output=True, text=True)
        return "ALL TESTS PASSED"
    except subprocess.CalledProcessError as e:
        return f"TESTS FAILED:\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}".strip()

@tool
def save_report(file_name_stem: str, markdown_content: str) -> str:
    base = Path(file_name_stem).stem
    md = WORKSPACE_DIR / f"{base}.md"
    html = WORKSPACE_DIR / f"{base}.html"
    md.write_text(markdown_content, encoding='utf-8')
    body = markdown.markdown(markdown_content, extensions=['fenced_code','tables'])
    html.write_text(f"<html><body>{body}</body></html>", encoding='utf-8')
    return f"Report saved as {base}.md and {base}.html"

@tool
def read_file(file_name: str) -> str:
    path = WORKSPACE_DIR / file_name
    if path.is_file():
        return path.read_text(encoding='utf-8')
    return f"Error: File not found: {file_name}"

file_system_tools = [save_file, run_tests, save_report]

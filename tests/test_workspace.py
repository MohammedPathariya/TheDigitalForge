import pytest

from backend.workspace import RunWorkspace


def test_workspaces_are_isolated() -> None:
    first = RunWorkspace()
    second = RunWorkspace()

    first.write("solution.py", "first")
    second.write("solution.py", "second")

    assert first.read("solution.py") == "first"
    assert second.read("solution.py") == "second"


@pytest.mark.parametrize(
    "path", ["/tmp/solution.py", "../solution.py", "src/../../x.py"]
)
def test_workspace_rejects_paths_outside_the_run(path: str) -> None:
    workspace = RunWorkspace()

    with pytest.raises(ValueError):
        workspace.write(path, "unsafe")

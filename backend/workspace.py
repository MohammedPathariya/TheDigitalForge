"""Isolated per-run virtual workspace."""

from pathlib import PurePath


class RunWorkspace:
    """A virtual file system owned by exactly one run."""

    def __init__(self) -> None:
        self._files: dict[str, str] = {}

    @staticmethod
    def normalize(file_path: str) -> str:
        path = PurePath(file_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(
                "Workspace paths must be relative and cannot contain '..'."
            )
        normalized = str(path)
        if normalized in {"", "."}:
            raise ValueError("Workspace path must name a file.")
        return normalized

    def write(self, file_path: str, content: str) -> str:
        normalized = self.normalize(file_path)
        self._files[normalized] = content
        return normalized

    def read(self, file_path: str) -> str | None:
        return self._files.get(self.normalize(file_path))

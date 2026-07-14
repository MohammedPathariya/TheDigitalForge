import os
from pathlib import Path

TEST_RUNTIME_ROOT = Path(".pytest_cache/runtime").resolve()
os.environ["HOME"] = str(TEST_RUNTIME_ROOT / "home")
os.environ["XDG_CONFIG_HOME"] = str(TEST_RUNTIME_ROOT / "config")
os.environ["XDG_DATA_HOME"] = str(TEST_RUNTIME_ROOT / "data")
os.environ["CREWAI_STORAGE_DIR"] = str(TEST_RUNTIME_ROOT / "crewai")

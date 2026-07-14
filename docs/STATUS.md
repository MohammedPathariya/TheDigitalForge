# Digital Forge Status

## Current phase

Day 1, Stabilize the foundation, is complete on `mjp/revamp-digital-forge`.

## Completed work

- Consolidated the backend into `backend.main`, which exposes the FastAPI app and the
  optional CLI entry point. Removed the broken legacy CLI, Flask server, deployment
  wrapper, and duplicate backend requirements file.
- Moved orchestration into `backend.pipeline` and converted imports to package-relative
  imports.
- Added typed settings, API request and response models, development plans, run status,
  and per-run workflow state. Configuration is loaded from environment variables without
  requiring an API key during health checks or module import.
- Replaced the shared global workspace and import-time agent/task instances with a fresh
  workspace, tools, agents, and tasks for every run. Workspace paths cannot be absolute or
  traverse outside the run.
- Disabled CrewAI agent memory because its default persistent storage is process-wide and
  not scoped by run. The current workflow passes all required context explicitly, so this
  prevents cross-run memory leakage without removing required behavior.
- Expanded typed run state to track lifecycle status, the technical brief, validated
  development plan, attempt count, test results, and final report.
- Lazy-loaded CrewAI so importing or health-checking the API does not trigger CrewAI's
  credential-storage side effects.
- Pinned direct runtime and development dependencies and generated `requirements.lock`
  with the complete resolved dependency graph. Standardized local, Conda, and CI checks on
  Python 3.11.
- Added Ruff, mypy, pytest, and GitHub Actions configuration plus focused tests for API
  validation, typed configuration limits, workspace isolation, full pipeline-object
  isolation, disabled agent memory, and typed run-state outputs.

## Verification performed

- Clean dependency resolution from `requirements-dev.txt` succeeded in a Python 3.11
  virtual environment.
- `ruff check .` passed.
- `ruff format --check backend tests` passed.
- `mypy backend tests` passed with 14 source files checked.
- `python -m pytest` passed with 12 tests.
- `python -m pip check` reported no broken requirements.
- Importing `backend.main:app` succeeded without an API key or CrewAI storage writes.
- Constructing `DevelopmentCrew` with a test key and isolated temporary home succeeded
  with four fresh agents and a unique run identifier. No model request was made.
- Constructing two pipelines proved that run IDs, workspaces, generated files, agents, and
  tasks are distinct and that no agent owns persistent memory.
- `git diff --check` passed.

## Known risks and deferred work

- A paid, end-to-end model run was intentionally not executed, so live OpenAI and CrewAI
  behavior remains unverified. The pipeline constructor and all local boundaries were
  verified without incurring external API cost.
- Generated code still executes through a local pytest subprocess. It is not a security
  boundary; Docker and Modal isolation are scheduled for Day 3.
- Agent-generated tests still determine current live-run success. Independent benchmark
  evaluators are the next phase.
- FastAPI and CrewAI emit upstream deprecation warnings during tests. They do not affect
  the passing checks but should be reevaluated when dependency versions change.
- The Streamlit frontend remains blocking and points at the existing hosted URL. Replacing
  it is intentionally deferred to Day 6.

## Decisions added or changed

No architecture decisions changed. Python 3.11 is now the verified runtime used by the
dependency lock and automated checks.

## Exact next task

Implement Day 2, Build the benchmark: create 20 independently authored LeetCode-inspired
tasks split into 10 easy and 10 medium tasks; add versioned task metadata and immutable
hidden evaluator tests that are never exposed to agents; define structured result
artifacts; and implement a zero-shot baseline runner. Keep sandbox implementation out of
Day 2 and use the current local runner interface only until Day 3.

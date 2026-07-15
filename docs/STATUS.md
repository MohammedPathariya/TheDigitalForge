# Digital Forge Status

## Current phase

Day 3, Build sandbox execution, is complete on `mjp/revamp-digital-forge`.

## Completed work

- Added a typed `SandboxRunner` contract with immutable request, file, resource-limit,
  and result models. Results include stdout, stderr, exit status, duration, timeout state,
  and infrastructure errors.
- Added `DockerSandboxRunner` for local and CI execution. Containers run as a non-root
  user with no network, a read-only root filesystem and source mount, dropped Linux
  capabilities, no-new-privileges, bounded memory and swap, fractional CPU limits, a PID
  limit, a bounded temporary filesystem, and both container and host wall timeouts.
- End-of-phase review closed a Docker cleanup gap by assigning each container a unique
  name and force-removing it when the host-side CLI timeout fires, preventing an orphaned
  sandbox from continuing to consume resources.
- Post-push CI diagnosis fixed benchmark input delivery by keeping Docker stdin attached.
  The regression was invisible to the simple smoke test because only benchmark execution
  sends serialized cases through stdin.
- Added a pinned Python 3.11 Docker image with pytest and a restricted `.dockerignore` so
  repository files, Git data, virtual environments, and `.env` secrets are never sent to
  the Docker build context.
- Added `ModalSandboxRunner` for hosted execution using Modal Sandboxes. It applies hard
  CPU and memory limits, blocks outbound networking, enforces execution and sandbox
  lifetimes, limits child processes before dropping root privileges, copies only requested
  files, and always terminates and detaches the sandbox.
- Added typed settings for selecting Docker or Modal and configuring time, memory, CPU,
  process, image, and Modal app limits. The CrewAI pipeline now constructs the configured
  adapter once per run.
- Replaced the generated pytest tool's local subprocess with the shared sandbox contract.
  Only that run's generated code and test file enter the sandbox.
- Reworked benchmark evaluation so candidate code and inputs run in the configured
  sandbox while hidden expected outputs remain in the host evaluator. Candidate containers
  receive no repository mount and cannot read hidden evaluator files.
- Added Docker and Modal selection to the zero-shot benchmark CLI and recorded the chosen
  backend in schema version 1.1.0 benchmark reports.
- Added Modal 1.5.1 as a pinned direct dependency, regenerated the complete lockfile, and
  updated CI to build the sandbox image before running checks and the Docker smoke test.
- Added focused tests for path containment, Docker security flags and limits, Modal limits
  and cleanup, hidden-test separation, sandbox-backed benchmark scoring, configuration,
  generated pytest routing, and benchmark artifact metadata.

## Verification performed

- Clean dependency resolution regenerated `requirements.lock` with 166 packages and
  installed Modal 1.5.1 into the Python 3.11 virtual environment.
- Installed Modal 1.5.1 signatures were checked for Sandbox creation, command execution,
  filesystem access, stdin streaming, cleanup, CPU, memory, timeout, and network controls.
- `ruff check .` passed.
- `ruff format --check .` passed with 28 files checked.
- `mypy backend benchmark tests` passed with 28 source files checked.
- The sandbox image built successfully and both live Docker smoke tests passed, including
  benchmark evaluation with serialized hidden-case inputs.
- `python -m pytest` passed with all 32 tests, including both Docker integration tests.
- `python -m pip check` reported no broken requirements.
- `python -m benchmark --help` exposed Docker and Modal backend selection.
- `git diff --check` passed.

## Known risks and deferred work

- GitHub Actions must confirm the Docker stdin fix on its Ubuntu runner after the updated
  branch is published.
- Modal behavior is verified against the installed SDK and a contract-level fake, but no
  authenticated cloud sandbox was created. Credentials, workspace access, image build,
  cold-start behavior, and free-tier consumption remain unverified without spending or
  creating external resources.
- The application now requires the Docker sandbox image to be built before local pipeline
  or benchmark execution. Missing images and unavailable daemons return explicit
  infrastructure failures rather than falling back to unsafe host execution.
- Sandbox stdout and stderr are structured but are not yet size-capped, sanitized, or
  classified for agent repair prompts. Output bounding, failure classification, and
  evidence sanitization are intentionally deferred to Day 4.
- A paid zero-shot model run remains intentionally unexecuted, so live model generation
  followed by sandbox evaluation is not yet verified end to end.
- FastAPI and CrewAI continue to emit the previously recorded upstream deprecation
  warnings during the full test suite.

## Decisions added or changed

No architecture decisions changed. Day 3 implements D003 by using Docker for local and CI
execution and Modal Sandboxes for the hosted path. Hidden expected outputs remain owned by
the benchmark harness as required by D002.

## Exact next task

Implement Day 4, Implement self-healing: classify candidate, test, timeout, resource, and
infrastructure failures; capture and sanitize bounded stdout and stderr; convert failures
into targeted repair evidence for the responsible agent; repair and re-execute the
original code; enforce three total candidate attempts; and ensure infrastructure failures
do not consume an attempt. Do not begin ChromaDB or RAG work from Day 5.

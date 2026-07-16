# Digital Forge Status

## Current phase

Day 6, Rebuild the frontend, is complete on `mjp/revamp-digital-forge`.
Days 1 through 6 remain consistent with the current week plan, architecture, and
accepted decisions. Day 7 deployment work has not started.

## Completed work

- Replaced the Streamlit application with a Next.js 16.2.10 App Router frontend using
  React 19 and strict TypeScript. The frontend lives under `frontend/` with pinned npm
  dependencies, ESLint, a separate type-check command, and a production build command.
- Implemented the agreed light visual system: warm off-white canvas, flat white cards,
  restrained gold brand and running states, green success indicators, amber interrupted
  states, red confirmed failures, purple retrieval evidence, and dark code and log panels.
- Added the chip/circuit brand mark and a simplified small-size favicon. Added responsive
  desktop and mobile layouts, visible keyboard focus, reduced-motion handling, semantic
  landmarks, accessible labels, and status text that does not rely on color alone.
- Added request submission with validation, character count, example prompts, backend
  health and cold-start states, local active-run recovery, polling, elapsed time, and
  cooperative cancellation messaging.
- Added structured run views for the live agent pipeline, sanitized event history,
  technical brief, development plan, candidate attempts, failure classes, repair targets,
  generated application and test artifacts, test output, RAG source metadata, and the final
  report. Interrupted polling is shown as recoverable and does not mark a run as failed.
- Added a benchmark dashboard that reads immutable `benchmark-results/*/report.json`
  artifacts, presents model and evaluator metadata, aggregate metrics, easy and medium
  pass rates, filters, task-level outcomes, duration, and errors. When no measured report
  exists, it shows an explicit unmeasured state instead of fabricated results.
- Added process-local asynchronous run coordination around the existing pipeline with
  `POST /runs`, `GET /runs/{run_id}`, `POST /runs/{run_id}/cancel`, and `GET /benchmarks`.
  Preserved the synchronous `POST /run` endpoint for compatibility.
- Added typed run stages, bounded event records, attempt snapshots, generated artifacts,
  retrieval metadata, sanitized terminal errors, and cooperative cancellation checkpoints
  between expensive workflow stages.
- Removed the Streamlit entry point and its direct runtime dependencies. Regenerated the
  Python lockfile while constraining unrelated transitive versions to the prior lock.
- Live browser integration exposed that Athena can return structured JSON objects for
  `developer_task` and `tester_task` even though the workflow model stores strings. Added
  an explicit prompt constraint and deterministic object/list normalization so that valid
  structured plans no longer terminate a run.
- Clarified failed-run accounting after live browser testing: repeated sandbox
  infrastructure failures now end with an infrastructure-specific status message, and the
  frontend separates consumed candidate attempts from raw test execution records.
- Removed the long technical brief from the primary Overview screen after live UI review;
  the Overview now prioritizes current activity and the development plan.
- Refined the Overview panels after browser testing: current activity and development
  plan now use bounded card scrolling with custom scrollbars, and structured development
  plan instructions render as labeled sections instead of raw JSON strings. Inline
  numbered and dashed instruction text now becomes readable bullet lists.
- Tightened the live-agent contract so planning, implementation, testing, and repair keep
  exact function names, file names, return schemas, and edge-case behavior aligned. Syntax
  failures now provide explicit contract-preserving developer guidance.
- Corrected failed-result pipeline rendering so a successfully generated final report is not
  labeled as a Janus failure. Athena's latest repair target now identifies Hephaestus for
  application failures or Argus for invalid generated tests, with the final failure class as
  fallback. Infrastructure failures blame neither agent and unexpected pipeline exceptions
  mark the stage where execution stopped.
- Stabilized the live elapsed counter by decoupling it from the slower run polling cycle and
  calculating completed seconds from the current clock. Also clarified test-suite repair
  activity text and required Argus to save syntactically valid Python without Markdown fences.
- Prevented generated tests from adding unstated case-insensitive behavior or exact exception
  messages. Test repairs now explicitly remove unsupported assertions rather than preserving
  stricter interpretations of the user's request.
- Added a targeted PostCSS 8.5.19 override because Next.js 16.2.10 pins a version covered
  by a moderate-severity advisory. The override passes the frontend build and leaves the
  production dependency audit clean.

## Verification performed

- `python -m pytest -q` passed with 63 tests; the two live Docker integration tests were
  skipped because the local Docker daemon was unavailable.
- `ruff check .` passed.
- `ruff format --check .` passed with 42 Python files checked.
- `mypy backend benchmark rag tests` passed with 42 source files checked.
- `npm run lint` passed for the Next.js frontend.
- `npm run typecheck` passed with strict TypeScript checking.
- `npm run build` produced static frontend routes for `/`, `/benchmark`, and `/icon.svg`.
- `.venv/bin/pytest tests/test_pipeline.py::test_run_reports_infrastructure_exhaustion_separately
  tests/test_pipeline.py::test_repeated_infrastructure_failures_stop_without_consuming_attempt`
  passed.
- `.venv/bin/ruff check backend/pipeline.py tests/test_pipeline.py` passed.
- `.venv/bin/ruff format --check backend/pipeline.py tests/test_pipeline.py` passed.
- `.venv/bin/mypy backend tests` passed.
- Added self-healing coverage for application syntax failures routing to the developer with
  contract-preserving repair guidance.
- Added pipeline coverage for the corrected test-suite repair activity message.
- Added task-contract coverage that prevents Argus from asserting unstated casing behavior or
  exact exception messages.
- `npm install` audited 400 packages after the PostCSS override and reported zero known
  vulnerabilities.
- FastAPI tests cover synchronous compatibility, asynchronous run creation and polling,
  not-found responses, cooperative cancellation, request validation, retrieval metadata
  serialization, and an empty benchmark-artifact directory.
- Browser verification confirmed the landing page, backend health indicator, example and
  clear controls, benchmark empty state, failed-run state, corrected failed-stage pipeline
  rendering, desktop layout, mobile layout, and absence of browser console errors.
- One live-model browser integration attempt completed Janus briefing and Athena planning,
  then exposed the structured-plan validation issue described above. The run was stopped,
  the issue was corrected and covered by a deterministic test, and another paid run was
  intentionally not started.
- `git diff --check` passed after implementation.

## Known risks and deferred work

- Run snapshots are process-local and disappear when the backend restarts. Durable or
  shared run storage is deferred until deployment requirements are finalized.
- Cancellation is cooperative. A request stops at the next workflow boundary but cannot
  interrupt a CrewAI or model request already in progress.
- The public one-run concurrency limit, rate limits, request timeouts, and model spending
  controls remain Day 7 work. The local Day 6 run manager does not claim those protections.
- No real algorithm benchmark report is currently present under `benchmark-results/`, so
  the verified dashboard correctly shows an unmeasured state. Full benchmark configurations
  remain after-week measurement work.
- A paid end-to-end run was not repeated after the structured-plan correction. Local tests
  cover normalization and workflow boundaries, but final live-model output quality remains
  to be reverified deliberately.
- Live Docker execution was not reverified because the local daemon was unavailable. Modal
  remains verified against the installed SDK and contract-level fakes, not an authenticated
  cloud sandbox.
- The deterministic RAG index remains intentionally small and version-pinned. The known
  retrieval-quality and library-upgrade constraints from Day 5 still apply.
- Agent-generated code can still fail after repair despite stronger contracts because live
  model output is nondeterministic. Such runs remain correctly marked failed and should be
  retained as quality evidence rather than counted as successful executions.
- FastAPI, CrewAI, Starlette, and OpenTelemetry continue to emit upstream deprecation
  warnings during the Python test suite.

## Decisions added or changed

No architecture decision changed. Day 6 implements D005 by replacing Streamlit with
Next.js and TypeScript and adding typed background run state, polling, and cancellation.
The benchmark dashboard continues to follow D001 and D007 by displaying only precomputed,
measured artifacts and never triggering or inventing benchmark results.

## Exact next task

Implement Day 7, Deploy and verify: deploy the frontend to Vercel, deploy FastAPI and
CrewAI to Render Free, connect hosted execution to Modal, add rate limits, request
timeouts, one-run concurrency, and model spending controls, then run deployment smoke
tests and finish project documentation. Do not run full benchmark configurations or update
resume and LinkedIn claims until the separate measured-results work begins.

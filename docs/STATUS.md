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
  `developer_task` and `tester_task` even though the workflow contract requires prose.
  Athena now uses typed output and nested plan instructions are rejected instead of being
  normalized into misleading example data.
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
- Added one pinned offline sandbox capability set shared by Docker, Modal, and agent prompts.
  It covers the bundled documentation libraries plus pytest and HTTP testing support without
  enabling network access or arbitrary per-run installation.
- Generalized missing-module handling: unavailable declared dependencies are non-retryable
  system configuration failures that consume no candidate attempt, while unrequested imports
  are routed to the application or test author that introduced them.
- Added library-aware retrieval filtering. Explicit library queries now exclude other
  libraries, and queries with no lexical relevance return no evidence instead of padded noise.
- Tightened ambiguous-contract handling so planning and tests do not invent normalization,
  response bodies, validation behavior, or other semantics absent from the request.
- Added Pydantic's pinned email-validation runtime to the shared offline sandbox capability
  set. `EmailStr` models now execute in Docker, and a stale image is classified as a
  non-retryable system configuration failure instead of consuming three candidate attempts.
- Added explicit active-agent state to run snapshots. The frontend now moves to Argus while
  the test suite is being authored, keeps unresolved application or test failures visible
  while Janus writes the report, and labels terminal failed runs as `Needs manual review`
  instead of the misleading `Complete`. Activity-message and stage fallbacks preserve the
  live highlight when viewing a snapshot from an older backend process.
- Required development plans, implementations, and generated tests to share the same public
  class names as well as function names, reducing model/test import drift on nested Pydantic
  tasks.
- Removed horizontal scrolling from development plans. The two plan columns can now shrink
  within their panel, and long filenames, field values, and list items wrap in place while
  the existing vertical scrolling remains available.
- Added a targeted PostCSS 8.5.19 override because Next.js 16.2.10 pins a version covered
  by a moderate-severity advisory. The override passes the frontend build and leaves the
  production dependency audit clean.
- Disabled CrewAI tool-result caching for every agent. Mutable `save_file` and `run_tests`
  calls can no longer replay stale outputs across development and repair stages.
- Made the original user request an immutable input to planning, implementation, test
  authoring, and failure analysis instead of relying on generated briefs and plans alone.
- Added deterministic generated-artifact validation. Invalid Python is rejected before it
  overwrites a workspace file, explicit backtick-delimited function contracts are checked
  before sandbox execution, and generated tests must import the real application module
  rather than embedding a replacement implementation.
- Routed deterministic request-contract failures directly to Hephaestus and test-artifact
  failures directly to Argus, avoiding an unnecessary Athena diagnosis call.
- Tightened plan and test reliability after a live feature-flag regression. Athena now emits
  the typed `DevelopmentPlan` schema with prose implementation logic instead of nested example
  data, all agents use temperature zero, and repaired test suites must re-audit every assertion
  against the original request before execution.
- Corrected the typed-plan integration after localhost verification exposed that CrewAI renders
  `CrewOutput.__str__()` as a Pydantic representation rather than JSON. The pipeline now reads
  typed `pydantic` and `json_dict` output directly before falling back to JSON text parsing.
- Added deterministic test-import normalization after Argus repeatedly preserved a placeholder
  module during repair. Imports of explicitly requested functions now target the planned
  application module before artifact validation, without changing test assertions.
- Changed test-owned semantic repair to discard the invalid generated suite before asking Argus
  for a fresh suite. This prevents incorrect expected values from anchoring subsequent repairs
  while preserving the original request and typed testing plan as the source of truth.
- Added benchmark checkpointing and guarded early-stop support. Each completed task now writes a
  task-level checkpoint before the aggregate report is finalized, and benchmark CLI runs can stop
  after a configured consecutive-failure streak unless the suite is already near completion.

## Verification performed

- Paid localhost verification on 2026-07-22 confirmed one valid repaired pass and one false
  positive. Feature-flag run `a1f3db16` corrected an invalid generated expectation and passed
  on attempt two. Normalization run `4a93f7cd` reported success on attempt three, but its final
  code violated the original display-name fallback and active-string normalization rules, so it
  must not be counted as a successful run. Further paid prompts were stopped.
- Paid guarded benchmark verification on 2026-07-23 completed the active v1.1.0 Digital Forge
  `gpt-4o-mini` run at 16/20 overall, with 9/10 easy and 7/10 medium tasks passing. The measured
  report is `benchmark-results/46e08fb1861141cf82fad76ef676ce5b/report.json`, with checkpoints
  under `benchmark-results/46e08fb1861141cf82fad76ef676ce5b/checkpoints/`. Failed tasks were
  `forge_easy_07`, `forge_medium_01`, `forge_medium_02`, and `forge_medium_06`.
- Paid zero-shot `gpt-4` verification on 2026-07-23 completed a v1.1.0 comparison run
  at 15/20 overall, with 8/10 easy and 7/10 medium tasks passing. That report is archived at
  `benchmark-results/ce0abe92172b45508794eb5e25928f70/report.json.archived` while the dashboard
  keeps the same-model `gpt-4o-mini` comparison active.
- After the feature-flag reliability fix, `.venv/bin/pytest -q` passed with 86 tests
  and five environment-dependent tests skipped. Ruff checks and formatting, mypy,
  frontend lint and type-check, the production frontend build, and a local browser
  smoke test also passed without submitting another paid model request.
- `.venv/bin/pytest -q` passed with 86 tests and five environment-dependent tests skipped
  after the benchmark-driven orchestration fixes.
- `ruff check backend benchmark rag tests`, `ruff format --check backend benchmark rag tests`,
  `mypy backend benchmark rag tests`, and `git diff --check` passed after those fixes.
- Replayed deterministic validation against the six interrupted v1.1.0 candidates without
  API calls. It identified the renamed `load_inventory_deltas` contract and the invalid
  `route_ticket` syntax before sandbox execution.
- `.venv/bin/pytest -q` passed with 80 tests, including five live Docker integration paths
  for basic isolation, declared-package imports, Pydantic `EmailStr`, the hidden benchmark
  evaluator, and FastAPI `TestClient` execution.
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
- Added mixed regression coverage for shared Docker and Modal capabilities, supported and
  unrequested missing modules, non-retryable infrastructure failures, explicit-library RAG
  filtering, and zero-relevance retrieval.
- Rebuilt `digital-forge-sandbox:py311` from the shared pinned requirements and verified the
  FastAPI application category that previously failed because the stale image contained only
  pytest.
- `npm install` audited 400 packages after the PostCSS override and reported zero known
  vulnerabilities.
- FastAPI tests cover synchronous compatibility, asynchronous run creation and polling,
  not-found responses, cooperative cancellation, request validation, retrieval metadata
  serialization, and an empty benchmark-artifact directory.
- Browser verification confirmed the landing page, backend health indicator, example and
  clear controls, benchmark empty state, failed-run state, corrected failed-stage pipeline
  rendering, desktop layout, mobile layout, and absence of browser console errors.
- Browser smoke verification after the active-agent UI change confirmed the frontend still
  renders the landing workflow without layout or runtime errors. A fresh live failed run was
  not started solely to reproduce the terminal review state.
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
- The zero-shot `gpt-4` algorithm benchmark is now measured at 18/20 overall,
  with 9/10 easy and 9/10 medium tasks passing on historical benchmark v1.0.0.
  That suite overemphasized single-function algorithm tasks and is no longer the
  active comparison suite. Benchmark v1.1.0 now mixes workflow-data,
  validation, reconciliation, reporting, configuration, and state-management
  tasks. Old v1.0.0 reports are preserved but filtered out of the active
  dashboard.
- The Digital Forge v1.0.0 comparison remains incomplete: a one-task smoke run
  scored 0/1, and the official run was stopped during its fourth task because
  model usage was too expensive. The interrupted run has no aggregate score and
  must not be used for claims. See `docs/BENCHMARK_INITIAL_RESULTS.md` for the
  preserved artifacts and findings.
- The active v1.1.0 zero-shot `gpt-4o-mini` baseline has been measured at 14/20
  overall, with 7/10 easy and 7/10 medium tasks passing. The valid report is
  `benchmark-results/3da7bfb192c84a47aedc04a1d20be0f7/report.json`. Two invalid zero-token
  pre-runs were quarantined by renaming their `report.json` files so
  the benchmark dashboard only loads measured v1.1.0 results.
- The first active v1.1.0 Digital Forge `gpt-4o-mini` run was stopped during
  `forge_easy_07` at the user's request. No aggregate score is available because
  the runner writes `report.json` only after all selected tasks finish. Six
  persisted candidates were re-evaluated locally with Docker; only
  `forge_easy_05` passed. The interrupted artifact is
  `benchmark-results/8afe20c0708f45a693c903445e75f91b/interrupted.json`.
- The structural causes found in that interrupted run are now fixed and remeasured: stale CrewAI
  tool caching is disabled, the original request is preserved through every code-producing
  stage, invalid function/import/syntax artifacts fail deterministic preflight checks, and the
  guarded 2026-07-23 run completed at 16/20 on v1.1.0.
- The benchmark runner now checkpoints task results, but it still does not capture CrewAI token
  usage and cost. Add spending limits, resumable execution, and usage telemetry before another
  expensive benchmark run.
- The local Digital Forge default model has been changed from CrewAI's effective
  `gpt-4` default to explicit `gpt-4o-mini` via `OPENAI_MODEL_NAME` to reduce
  routine localhost and pilot-run cost. Use an explicit model override only for
  deliberate paid comparisons.
- A paid end-to-end run was not repeated after the structured-plan correction. Local tests
  cover normalization and workflow boundaries, but final live-model output quality remains
  to be reverified deliberately.
- Modal capability construction remains verified against the installed SDK signature and
  contract-level fakes, not an authenticated cloud sandbox build. Hosted verification remains
  part of Day 7 deployment work.
- Existing local Docker images must be rebuilt after sandbox capability changes; otherwise
  the pipeline now reports the stale image as a non-retryable system failure without consuming
  candidate attempts.
- The deterministic RAG index remains intentionally small and version-pinned. The known
  retrieval-quality and library-upgrade constraints from Day 5 still apply.
- Agent-generated code can still fail after repair despite stronger contracts because live
  model output is nondeterministic. Such runs remain correctly marked failed and should be
  retained as quality evidence rather than counted as successful executions.
- Generated tests can still create a false positive by asserting behavior that contradicts the
  original request and then driving application repair toward those assertions. A terminal
  `ALL TESTS PASSED` result is not trustworthy until an independent final contract audit compares
  the resulting application directly with the immutable user request.
- FastAPI, CrewAI, Starlette, and OpenTelemetry continue to emit upstream deprecation
  warnings during the Python test suite.

## Decisions added or changed

D008 now defines the shared offline sandbox capability contract and failure ownership for
missing modules. Day 6 continues to implement D005 through Next.js, typed background run
state, polling, and cancellation. The benchmark dashboard continues to follow D001 and D007
by displaying only precomputed, measured artifacts and never triggering or inventing results.

## Exact next task

Add an independent final contract audit that cannot treat generated tests as the source of truth.
It must compare the final application directly with the immutable request and block a successful
status when repaired code drops or contradicts a requirement. Then finish benchmark checkpointing,
usage telemetry, and spending limits before another paid pilot or any resume claim update.

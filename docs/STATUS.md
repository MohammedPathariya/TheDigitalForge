# Digital Forge Status

## Current phase

Day 2, Build the benchmark, is complete and end-of-phase reviewed on
`mjp/revamp-digital-forge`.

## Completed work

- Added a versioned benchmark catalog with 20 independently authored,
  LeetCode-inspired Python tasks split into 10 easy and 10 medium tasks. Each task
  has a stable ID, semantic version, function contract, tags, and time limit.
- Added 94 evaluator-only hidden cases stored separately from public task prompts.
  Case collections and nested inputs are immutable tuples exposed through a read-only
  mapping.
- Added a deterministic SHA-256 digest for the hidden evaluator cases so every result
  artifact identifies the exact evaluator data used.
- Added a local subprocess evaluator that loads one candidate, enforces the task time
  limit, returns structured pass counts, and avoids disclosing hidden inputs or expected
  outputs in failure messages.
- Added typed, versioned result models for generated solutions, per-task evaluations,
  and complete benchmark reports. Each run writes candidate files and `report.json` to
  a unique run directory.
- Added a zero-shot baseline runner using the OpenAI Responses API. It sends only the
  public task prompt, requires an explicit model ID for reproducibility, records response
  and token metadata, and supports running all tasks or selected task IDs.
- Declared the OpenAI SDK as a direct runtime dependency. The existing lock already pins
  the same `openai==2.45.0` version.
- Expanded CI type checking to cover the new `benchmark` package and added focused tests
  for catalog balance, hidden-case coverage and immutability, evaluator behavior, prompt
  separation, code extraction, and structured artifacts.
- Corrected two hidden expected outputs found during end-of-phase reference validation:
  one non-palindrome was incorrectly marked valid, and one nearest-pair tie did not follow
  the documented lexicographic rule. Added regression candidates for both tasks.

## Verification performed

- Catalog inspection confirmed 20 unique tasks, 10 easy tasks, 10 medium tasks, and 94
  hidden cases.
- Independent recomputation confirmed the corrected palindrome result is false and the
  corrected nearest-pair result is `[0, 3]` under the task's tie-break rule.
- `python -m benchmark --help` succeeded and exposed the model, task-selection, and
  output arguments.
- `ruff check .` passed.
- `ruff format --check .` passed with 25 files checked.
- `mypy backend benchmark tests` passed with 25 source files checked.
- `python -m pytest` passed with 22 tests.
- `python -m pip check` reported no broken requirements.
- `git diff --check` passed.

## Known risks and deferred work

- A paid zero-shot model run was intentionally not executed. The OpenAI request boundary
  is implemented and locally type-checked, but live credentials, model access, cost, and
  end-to-end API behavior remain unverified.
- Candidate code still runs in a local subprocess. Timeouts limit duration but do not
  provide filesystem, network, memory, CPU, or process isolation. Benchmark candidates
  must remain trusted until Day 3 sandbox adapters replace this runner.
- Hidden tests are separated from model prompts and their values are not emitted in
  failure artifacts, but repository-level secrecy is not a security boundary. Day 3
  sandboxing must prevent candidate code from reading evaluator files.
- Lockfile regeneration could not complete because dependency resolution required blocked
  network access. The existing lock already contains the exact declared OpenAI SDK
  version, so installs are unchanged; only the generated provenance comment was not
  refreshed.
- FastAPI and CrewAI continue to emit the previously recorded upstream deprecation
  warnings during the full test suite.

## Decisions added or changed

No architecture decisions changed. The benchmark follows D001, D002, D004, and D007 by
keeping public prompts separate from hidden evaluation, producing reproducible artifacts,
and requiring measured results before claims are updated.

## Exact next task

Implement Day 3, Build sandbox execution: define a typed `SandboxRunner` contract; add a
Docker implementation for local and CI benchmark runs and a Modal implementation for the
hosted demo; enforce time, memory, CPU, process, and network limits; prevent candidate
access to hidden evaluator files; and return structured stdout, stderr, exit status,
duration, timeout status, and test results. Do not begin self-healing work from Day 4.

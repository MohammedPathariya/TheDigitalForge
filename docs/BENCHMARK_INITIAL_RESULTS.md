# Historical Benchmark Results

## Comparison status

These results are for benchmark version `1.0.0`. They are preserved for audit
history only. The active benchmark suite is now `1.1.0`, which adds structured
workflow, validation, reconciliation, and normalization tasks. Do not compare
new `1.1.0` results against the old `1.0.0` reports.

The zero-shot GPT-4 baseline was complete on v1.0.0. The Digital Forge GPT-4 run
was not complete and must not be presented as a 20-task comparison.

| Configuration | Scope | Passed | Pass rate | Status |
| --- | ---: | ---: | ---: | --- |
| Zero-shot `gpt-4` | 20 tasks | 18 | 90% | Complete |
| Digital Forge `gpt-4` smoke | 1 task | 0 | 0% | Complete smoke only |
| Digital Forge `gpt-4` official run | 20 intended | N/A | N/A | Interrupted |

All recorded evaluations below use benchmark version `1.0.0`, Docker, and
evaluator SHA-256
`1519f9926a878c110fb5e92725ebc3bb569a8672df6f6e83dfac28a14a999eb5`.
The dashboard now filters reports to the active benchmark version, so these old
reports can remain on disk without being shown as current evidence.

## Zero-shot GPT-4

- Run ID: `837bd174c25545baaa7842397564aa70`
- Overall: 18/20
- Easy: 9/10
- Medium: 9/10
- Recorded usage: 2,145 input tokens and 1,940 output tokens
- Failed tasks: `forge_easy_04` and `forge_medium_10`

The complete report and all 20 candidates are stored under
`benchmark-results/837bd174c25545baaa7842397564aa70/`.

## Digital Forge GPT-4

The smoke run on `forge_easy_01` took about 4 minutes 23 seconds and failed all
four hidden cases because the generated application did not preserve the
requested top-level function contract. Its run ID is
`212abe3e6e0b4394b82e1e418b09ba89`.

The official run ID `5d3c03b3f73945dfb10f4f25fb1bea58` was stopped during
`forge_easy_04`. One candidate was persisted before interruption:
`forge_easy_02`, which passed 4/4 hidden cases. Missing candidates and the lack
of a final `report.json` mean this run has no valid aggregate score.

Observed cost and reliability problems during the Digital Forge run:

- Multiple GPT-4 calls and repair calls were required per task.
- Planning sometimes changed a requested top-level function into a class or a
  different return schema.
- Generated tests repeatedly imported module names that did not match the
  generated application filename.
- CrewAI tool caching replayed stale `run_tests` and `save_file` results during
  some repairs.
- The run reached the account's 10,000 token-per-minute GPT-4 limit and retried.
- The current pipeline does not record per-agent token usage or exact cost.
- The benchmark runner writes `report.json` only at the end, so interruption
  loses task-level result records even when some candidates were generated.

## Recalibration

## Active v1.1.0 zero-shot baseline

The first active-suite zero-shot baseline was run with `gpt-4o-mini` only. No
Digital Forge or CrewAI calls were made.

- Run ID: `3da7bfb192c84a47aedc04a1d20be0f7`
- Overall: 14/20
- Easy: 7/10
- Medium: 7/10
- Recorded usage: 3,166 input tokens and 3,334 output tokens
- Evaluator SHA-256:
  `cc95a687dc7e8200dde2700ad87d744b3f0dbe004bd6d9285c17bb3beefc3f2b`
- Failed tasks: `forge_easy_01`, `forge_easy_06`, `forge_easy_07`,
  `forge_medium_02`, `forge_medium_04`, and `forge_medium_06`

The complete report and all 20 candidates are stored under
`benchmark-results/3da7bfb192c84a47aedc04a1d20be0f7/`.

Two invalid pre-runs were quarantined by renaming their `report.json` files so
they do not appear in the benchmark dashboard:

- `benchmark-results/d4691be4738e430286b01467d89edfb5/wrong-model-gpt4-report.json`
- `benchmark-results/35c90c494df044d288eedf8c26f1f211/api-connection-error-report.json`

Both invalid pre-runs recorded zero response IDs and zero token usage.

## Interrupted v1.1.0 Digital Forge run

The first active-suite Digital Forge run used `digital-forge:gpt-4o-mini` and
was stopped at the user's request during `forge_easy_07`.

- Run ID: `8afe20c0708f45a693c903445e75f91b`
- Intended scope: 20 tasks
- Persisted candidates: 6
- Persisted candidate score: 1/6
- Passed persisted task: `forge_easy_05`
- Failed persisted tasks: `forge_easy_01`, `forge_easy_02`, `forge_easy_03`,
  `forge_easy_04`, and `forge_easy_06`
- Aggregate score: unavailable because no `report.json` was written

Observed failure modes:

- Public function contract drift, such as `process_inventory` instead of the
  requested `load_inventory_deltas`.
- Placeholder test imports, including `your_module`, `application_module`, and
  `your_application_module`.
- Tool caching replayed stale `run_tests` and `save_file` results during repair.
- Generated tests sometimes embedded a replacement implementation instead of
  importing and testing the candidate module.
- The current Digital Forge benchmark path still has no per-call token or cost
  telemetry.

The interrupted artifact is stored at
`benchmark-results/8afe20c0708f45a693c903445e75f91b/interrupted.json`.

Corrections completed after this interrupted run:

- CrewAI tool caching is disabled for all four agents.
- The immutable original request is passed to planning, implementation, testing,
  and repair analysis.
- Python syntax is validated before generated files overwrite the workspace.
- Explicit public function names and real application imports are validated before
  sandbox execution.
- Contract failures route directly to the developer and invalid test artifacts route
  directly to the tester.

Remaining work before another paid Digital Forge benchmark:

1. Persist each task result immediately and add resume support.
2. Record tokens, estimated cost, model, agent, attempt, and elapsed time for
   every model call.
3. Add a hard per-run token or dollar budget and a per-task timeout.
4. Run a three-task pilot before authorizing another 20-task run.

No resume or portfolio claim should use a Digital Forge improvement percentage
until a complete comparable run exists.

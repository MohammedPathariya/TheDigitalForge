# Guarded Digital Forge Benchmark Run, 2026-07-23

## Summary

- Benchmark version: `1.1.0`
- Digital Forge model label: `digital-forge:gpt-4o-mini`
- Digital Forge run ID: `46e08fb1861141cf82fad76ef676ce5b`
- Digital Forge result: `16/20`
- Easy tasks: `9/10`
- Medium tasks: `7/10`
- Started: `2026-07-23T02:11:13.710275Z`
- Completed: `2026-07-23T02:20:27.497262Z`
- Report: `benchmark-results/46e08fb1861141cf82fad76ef676ce5b/report.json`

## Baseline Comparison

- Zero-shot model: `gpt-4o-mini`
- Zero-shot run ID: `3da7bfb192c84a47aedc04a1d20be0f7`
- Zero-shot result: `14/20`
- Zero-shot easy tasks: `7/10`
- Zero-shot medium tasks: `7/10`
- Zero-shot report: `benchmark-results/3da7bfb192c84a47aedc04a1d20be0f7/report.json`
- Net measured lift: `+2` tasks over zero-shot `gpt-4o-mini` on benchmark v1.1.0.

The zero-shot `gpt-4` v1.1.0 run scored `15/20` and is archived at
`benchmark-results/ce0abe92172b45508794eb5e25928f70/report.json.archived`.

## Guardrails

- Per-task checkpoints were written to `benchmark-results/46e08fb1861141cf82fad76ef676ce5b/checkpoints/`.
- The run used `--max-consecutive-failures 3`.
- The run used `--finish-remaining-threshold 3`.
- The guardrail did not interrupt the run because no early three-failure streak occurred.

## Failed Tasks

| Task | Tests | Error |
| --- | ---: | --- |
| `forge_easy_07` | `2/4` | `hidden case failed during hidden case 2` |
| `forge_medium_01` | `0/4` | `hidden case failed during hidden case 0` |
| `forge_medium_02` | `1/4` | `hidden case failed during hidden case 1` |
| `forge_medium_06` | `0/4` | `hidden case failed during hidden case 0` |

## Notes

- This run validates the active algorithm benchmark path, not the separate RAG evaluation suite.
- Argus repair behavior was exercised during the run, including generated-test import repair paths.
- Per-agent token and cost telemetry is still not captured by the benchmark runner.

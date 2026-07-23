# The Digital Forge

The Digital Forge is a multi-agent software generation system for turning a natural-language request into a tested Python implementation. It coordinates four specialized agents, executes generated code in an isolated sandbox, records repair attempts, and exposes both live run traces and precomputed benchmark evidence through a Next.js dashboard.

The current revamp branch is `mjp/revamp-digital-forge`.

## What It Does

- Accepts a user request for a small Python feature or service.
- Builds a technical brief and development plan.
- Generates application code and tests.
- Runs the generated artifacts in a network-isolated sandbox.
- Classifies failures as application, test, infrastructure, or contract issues.
- Repairs failed candidates within a bounded attempt budget.
- Records generated artifacts, execution output, retrieval evidence, and the final report.
- Displays immutable benchmark reports without spending model tokens in the public dashboard.

## Architecture

```text
Next.js frontend
        |
        v
FastAPI backend
        |
        v
CrewAI orchestration
Janus -> Athena -> Hephaestus -> Argus
             |                    |
             v                    v
      ChromaDB retrieval     SandboxRunner
                             |           |
                             v           v
                          Docker       Modal
                        local/CI    hosted demo
        |
        v
Structured run and benchmark artifacts
```

Agent roles:

- `Janus`: turns the request into a technical brief and final report.
- `Athena`: creates the typed development and testing plan.
- `Hephaestus`: writes and repairs application code.
- `Argus`: writes and repairs the generated test suite.

The benchmark evaluator is independent from the agents. Agent-generated tests support development, but hidden benchmark tests determine correctness.

## Current Benchmark Evidence

The active benchmark suite is version `1.1.0` with 20 tasks: 10 easy and 10 medium. It measures the algorithmic and workflow-code path, not the separate RAG evaluation suite.

| Run | Model | Result | Easy | Medium | Report |
| --- | --- | ---: | ---: | ---: | --- |
| Digital Forge | `digital-forge:gpt-4o-mini` | `16/20` | `9/10` | `7/10` | `benchmark-results/46e08fb1861141cf82fad76ef676ce5b/report.json` |
| Zero-shot baseline | `gpt-4o-mini` | `14/20` | `7/10` | `7/10` | `benchmark-results/3da7bfb192c84a47aedc04a1d20be0f7/report.json` |

The dashboard loads these tracked report artifacts through `GET /benchmarks`. Full benchmark execution happens locally or in CI, not in the public demo.

See `docs/BENCHMARK_GUARDED_RUN_2026_07_23.md` for the guarded run details.

## Repository Layout

```text
backend/             FastAPI app, run manager, pipeline integration
benchmark/           Benchmark catalog, runners, evaluator, hidden cases
benchmark-results/   Tracked benchmark report JSON files used by the dashboard
frontend/            Next.js App Router frontend
rag/                 Versioned ChromaDB documentation index
tests/               Backend, pipeline, sandbox, benchmark, and API tests
docs/                Architecture, decisions, status, and benchmark notes
```

## Requirements

- Python 3.10 or newer
- Node.js compatible with the pinned frontend dependencies
- Docker for local sandbox execution and benchmark reproduction
- OpenAI API key for live agent runs and benchmark generation

Create a local `.env` file when running model-backed paths:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL_NAME=gpt-4o-mini
```

The `.env` file is ignored by Git.

## Local Setup

Backend:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m backend.main
```

The backend defaults to `http://localhost:8000`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:3000` and calls the backend at `http://localhost:8000`. Override that with `NEXT_PUBLIC_BACKEND_URL` if needed.

## Running Benchmarks

Zero-shot baseline:

```bash
.venv/bin/python -m benchmark.baseline \
  --model gpt-4o-mini \
  --sandbox docker \
  --max-consecutive-failures 3 \
  --finish-remaining-threshold 3
```

Digital Forge:

```bash
.venv/bin/python -m benchmark.digital_forge \
  --model gpt-4o-mini \
  --sandbox docker \
  --max-consecutive-failures 3 \
  --finish-remaining-threshold 3
```

Each completed task writes a checkpoint before the aggregate report is finalized. A full successful run writes `benchmark-results/<run_id>/report.json`. Guarded interrupted runs write `interrupted.json`.

## Verification

Python checks:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check backend benchmark rag tests
.venv/bin/python -m ruff format --check backend benchmark rag tests
.venv/bin/python -m mypy backend benchmark rag tests
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Targeted benchmark/frontend checks used during the latest revamp:

```bash
.venv/bin/python -m pytest tests/test_benchmarks.py tests/test_baseline.py tests/test_digital_forge_benchmark.py -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

## Current Limits

- Run snapshots are process-local and disappear when the backend restarts.
- Cancellation is cooperative and stops at workflow boundaries.
- Public deployment rate limits, spend controls, durable run storage, and one-run concurrency enforcement remain deployment work.
- Per-agent token and cost telemetry is not yet captured by the benchmark runner.
- The RAG layer is evaluated separately from the active 20-task algorithm benchmark.

## Project Docs

- `docs/STATUS.md`: current implementation status, verification, risks, and handoff notes.
- `docs/ARCHITECTURE.md`: system architecture and deployment model.
- `docs/DECISIONS.md`: accepted design decisions.
- `docs/WEEK_PLAN.md`: phased revamp plan.
- `docs/BENCHMARK_GUARDED_RUN_2026_07_23.md`: latest guarded benchmark evidence.

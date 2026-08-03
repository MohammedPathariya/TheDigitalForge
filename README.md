# The Digital Forge

The Digital Forge is a research portfolio project for studying whether a specialized multi-agent software workflow can produce more reliable Python implementations than a single-pass baseline.

The system accepts a natural-language request, creates a technical brief and typed development plan, generates application code and tests, executes the candidate in an isolated sandbox, and performs bounded repairs when execution fails. Each run exposes its intermediate artifacts and evidence for inspection.

Live demo: [the-digital-forge-jade.vercel.app](https://the-digital-forge-jade.vercel.app/)

## Research framing

The project evaluates workflow design, not just model output. The four agents have separate responsibilities, generated tests are treated as development artifacts rather than authoritative evaluation, and benchmark correctness comes from independent hidden evaluators.

The main research questions are:

- Does role specialization improve task completion over a same-model zero-shot baseline?
- Does targeted failure classification make bounded self-healing useful without hiding failed candidates?
- Does isolated execution and version-pinned retrieval make generated code safer and more reproducible?

The current benchmark evidence is limited to the recorded configuration below. It is not a claim of general model superiority.

| Run | Model label | Result | Easy | Medium |
| --- | --- | ---: | ---: | ---: |
| Digital Forge | `digital-forge:gpt-4o-mini` | `16/20` | `9/10` | `7/10` |
| Zero-shot baseline | `gpt-4o-mini` | `14/20` | `7/10` | `7/10` |

Benchmark version `1.1.0` contains 20 tasks, split evenly between easy and medium difficulty. The full run was executed locally with Docker and recorded as immutable JSON artifacts. See the [guarded run report](docs/BENCHMARK_GUARDED_RUN_2026_07_23.md) for task-level evidence, guardrails, and report paths.

## System overview

```text
User request
    -> Next.js dashboard
    -> FastAPI run API
    -> Janus -> Athena -> Hephaestus -> Argus
    -> isolated candidate execution
    -> bounded repair loop
    -> final report, artifacts, logs, and retrieval evidence
```

The research architecture and deployment topology are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The request lifecycle and data contracts are documented in [docs/DATA_FLOW.md](docs/DATA_FLOW.md).

### Agent responsibilities

| Agent | Responsibility |
| --- | --- |
| Janus | Converts the request into a technical brief and writes the final report. |
| Athena | Converts the brief into a typed plan and diagnoses general failures. |
| Hephaestus | Writes and repairs the application implementation. |
| Argus | Writes and repairs the generated pytest suite and runs it. |

Documentation retrieval is available to the agents through a tool backed by a versioned ChromaDB index of pinned official documentation. Retrieval events are retained in the run state with source metadata.

## Repository layout

```text
backend/             FastAPI API, run manager, pipeline, agents, sandbox adapters
benchmark/           Task catalog, baseline, Digital Forge runner, evaluator
benchmark-results/   Immutable report artifacts consumed by the dashboard
frontend/            Next.js App Router interface
rag/                 Versioned documentation sources and ChromaDB index
tests/               Backend, sandbox, retrieval, benchmark, and API tests
docs/                Architecture, data flow, decisions, deployment, and evidence
```

## Local development

Requirements: Python 3.10 or newer, Node.js compatible with the pinned frontend dependencies, Docker for sandbox execution, and an OpenAI API key for model-backed runs.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Run the backend and frontend in separate terminals:

```bash
.venv/bin/python -m backend.main
cd frontend && npm ci && npm run dev
```

The backend listens on `http://localhost:8000`; the frontend listens on `http://localhost:3000`.

## Reproducing benchmark runs

Run the same-model baseline:

```bash
.venv/bin/python -m benchmark.baseline \
  --model gpt-4o-mini \
  --sandbox docker \
  --max-consecutive-failures 3 \
  --finish-remaining-threshold 3
```

Run the Digital Forge workflow:

```bash
.venv/bin/python -m benchmark.digital_forge \
  --model gpt-4o-mini \
  --sandbox docker \
  --max-consecutive-failures 3 \
  --finish-remaining-threshold 3
```

Each task writes a checkpoint. Completed runs write `report.json`; guarded interruptions write `interrupted.json` so incomplete evidence remains visible.

## Verification

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check backend benchmark rag tests
.venv/bin/python -m ruff format --check backend benchmark rag tests
.venv/bin/python -m mypy backend benchmark rag tests
cd frontend && npm run lint && npm run typecheck && npm run build
```

## Deployment and limits

The frontend is deployed on Vercel and the API is configured for Render. The hosted frontend, backend health connection, and benchmark dashboard were browser-verified on 2026-07-29. A complete hosted Modal code-generation run remains unverified and is not presented as a completed deployment claim. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

Important current limits:

- Run snapshots, workspaces, rate limits, and daily budgets are process-local and disappear on restart or scale-out.
- The public demo permits one active model-backed run at a time.
- Cancellation is cooperative and occurs at workflow boundaries.
- The benchmark measures the recorded task suite and configuration, not general software engineering ability.
- Retrieval is evaluated separately from the 20-task algorithm benchmark.

## Project documentation

- [Architecture and deployment topology](docs/ARCHITECTURE.md)
- [Request lifecycle and data flow](docs/DATA_FLOW.md)
- [Design decisions](docs/DECISIONS.md)
- [Deployment configuration and smoke tests](docs/DEPLOYMENT.md)
- [Current implementation status and verification](docs/STATUS.md)
- [Guarded benchmark evidence](docs/BENCHMARK_GUARDED_RUN_2026_07_23.md)

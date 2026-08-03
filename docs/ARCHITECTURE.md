# The Digital Forge architecture

This document describes the implemented system as of the current mainline. It separates the research workflow from the public deployment and benchmark paths.

## Logical architecture

```mermaid
flowchart LR
    U[User] --> UI[Next.js dashboard]
    UI --> API[FastAPI API]
    API --> RM[Process-local RunManager]
    RM --> PIPE[DevelopmentCrew]
    PIPE --> J["Janus<br/>brief and report"]
    PIPE --> A["Athena<br/>typed plan and diagnosis"]
    PIPE --> H["Hephaestus<br/>application code"]
    PIPE --> AR["Argus<br/>tests and validation"]
    PIPE --> WS["Per-run in-memory workspace"]
    PIPE --> RET[Retrieval tool]
    RET --> CH[Versioned ChromaDB index]
    WS --> SB[SandboxRunner]
    SB --> DOCKER["Docker sandbox<br/>local and CI"]
    SB --> MODAL["Modal sandbox<br/>hosted path"]
    PIPE --> E["Run events, attempts, artifacts, report"]
    E --> RM
    RM --> UI
```

The frontend uses asynchronous `POST /runs` submission and polls `GET /runs/{run_id}`. The API also retains a synchronous `POST /run` compatibility endpoint. `GET /benchmarks` reads tracked report files and does not start model execution.

## Deployment topology

```mermaid
flowchart TB
    B[Browser]
    V["Vercel<br/>Next.js frontend"]
    R["Render Free<br/>FastAPI and CrewAI"]
    M["Modal<br/>Hosted sandbox execution"]
    C["ChromaDB index<br/>Bundled with backend"]
    O["OpenAI API<br/>Model-backed agents"]
    L["Local or CI runner<br/>Docker and full benchmarks"]
    D["Docker sandbox image<br/>Pinned offline capability set"]

    B --> V
    V --> R
    R --> O
    R --> C
    R --> M
    L --> O
    L --> D
    L --> C
```

Render is not the Docker execution host, so the hosted configuration selects Modal. Local and CI benchmark runs select Docker. Both adapters implement the same sandbox contract and use the pinned capability set defined for generated code execution.

## Component responsibilities

### API and run coordination

`backend/main.py` exposes health, run submission, polling, cancellation, and benchmark-report endpoints. `RunManager` owns process-local snapshots, worker threads, cancellation events, the one-active-run limit, and the daily model-run budget. The API layer applies the per-client rate limit.

### Orchestration

`backend/pipeline.py` creates one `DevelopmentCrew` per request. The crew owns a `RunState`, a fresh `RunWorkspace`, the agent instances, file tools, retrieval tools, and a selected sandbox adapter. Agent outputs are converted into typed plans before implementation begins.

### Execution and self-healing

Generated Python and pytest files are syntax-checked before being saved. The sandbox receives only the two generated files, runs pytest with fixed time, memory, CPU, process, and network limits, and returns structured output. Failures are classified as application, test, infrastructure, timeout, resource, or contract failures. Candidate attempts are capped at three; retryable infrastructure failures do not consume a candidate attempt.

### Evidence

Each run records stage events, the technical brief, typed plan, generated artifacts, retrieval events, test output, candidate attempt history, and final report. Benchmark reports are separate immutable files with model, task, evaluator, sandbox, and task-level result metadata.

## Trust boundaries and state boundaries

```mermaid
flowchart LR
    REQUEST[Untrusted natural-language request]
    AGENTS[Model-generated artifacts]
    VALIDATE[Syntax and contract validation]
    SANDBOX[Network-isolated sandbox]
    REPORT[Sanitized evidence]

    REQUEST --> AGENTS
    AGENTS --> VALIDATE
    VALIDATE -->|accepted files only| SANDBOX
    VALIDATE -->|rejected artifact| REPORT
    SANDBOX --> REPORT
    REPORT --> UI[Inspectable run snapshot]
```

The in-memory workspace is scoped to one run and is not shared between requests. Run snapshots are also process-local. This keeps the public demo simple, but it means state is lost on restart and is not a durable production data store.

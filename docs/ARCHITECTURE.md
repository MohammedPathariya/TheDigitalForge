# Digital Forge Architecture

## Target system

```text
Next.js frontend
        |
        v
FastAPI service
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

## Main components

### Orchestration

The four specialized agents run through explicit, typed workflow state. Each run receives its own workspace and identifier. No mutable workspace is shared between requests.

### Benchmark

The benchmark owns its prompts, metadata, reference behavior, and hidden tests. Agent-generated tests can support development but cannot determine benchmark correctness.

### Sandbox

`SandboxRunner` provides one contract with two implementations:

- `DockerSandboxRunner` for local development, continuous integration, and benchmark reproduction.
- `ModalSandboxRunner` for the free-tier public demo.

Both return structured stdout, stderr, exit status, duration, timeout status, and test results.

### Self-healing

Failed executions are classified and converted into sanitized repair evidence. The original code is repaired and re-executed with a maximum of three total attempts. Infrastructure failures do not consume a candidate attempt.

### Retrieval

ChromaDB stores chunks from version-pinned official documentation. Retrieval results include source metadata and are logged with each run. The hosted backend uses a prebuilt index bundled with the deployment.

### Frontend

The Next.js interface submits runs, polls for status, displays attempts and evidence, and presents precomputed benchmark results. The public demo permits one active run at a time.

## Deployment

```text
Vercel Hobby
└── Next.js frontend

Render Free
├── FastAPI
├── CrewAI orchestration
└── Embedded ChromaDB index

Modal Starter
└── Hosted sandbox execution

Local and CI
└── Docker sandbox and full benchmark execution
```

The public demo uses free hosting tiers. Model API usage remains usage-based and must be protected with rate and spending limits.

# Digital Forge Revamp Week Plan

## Objective

Rebuild The Digital Forge into a reproducible multi-agent coding system with a benchmark, isolated execution, self-healing repairs, documentation retrieval, a modern frontend, and a free-tier public deployment.

## Day 1: Stabilize the foundation

- Consolidate the backend entry points.
- Replace shared global state with isolated per-run state.
- Add typed inputs, outputs, and configuration.
- Pin dependencies and establish automated checks.

## Day 2: Build the benchmark

- Create 20 independently written LeetCode-inspired tasks.
- Use 10 easy and 10 medium tasks.
- Add immutable hidden evaluator tests and task metadata.
- Implement the zero-shot baseline runner.

## Day 3: Build sandbox execution

- Define a common sandbox interface.
- Implement Docker execution for local and CI use.
- Implement Modal execution for the hosted demo.
- Enforce time, memory, CPU, process, and network limits.

## Day 4: Implement self-healing

- Classify execution failures.
- Capture and sanitize stdout and stderr.
- Route targeted repair instructions to the correct agent.
- Enforce a maximum of three total attempts.

## Day 5: Add ChromaDB RAG

- Ingest version-pinned official API documentation.
- Build and version the ChromaDB index.
- Give relevant agents a retrieval tool.
- Log retrieved sources and add a small API-focused evaluation suite.

## Day 6: Rebuild the frontend

- Replace Streamlit with Next.js and TypeScript.
- Add run submission, progress, attempts, logs, code, and RAG evidence views.
- Add a dashboard for precomputed benchmark results.
- Handle backend cold starts and interrupted runs clearly.

## Day 7: Deploy and verify

- Deploy the frontend to Vercel.
- Deploy the FastAPI and CrewAI backend to Render Free.
- Connect hosted execution to Modal.
- Add rate limits, timeouts, one-run concurrency, and spending controls.
- Run deployment smoke tests and finish project documentation.

## After the main week

- Run all benchmark configurations.
- Generate task-level result artifacts and aggregate metrics.
- Update the resume and LinkedIn claims to the measured results.
- Add screenshots, an architecture diagram, and a short demo video.

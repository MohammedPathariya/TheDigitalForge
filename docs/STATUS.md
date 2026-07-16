# Digital Forge Status

## Current phase

Day 5, Add ChromaDB RAG, is complete on `mjp/revamp-digital-forge`.
Days 1 through 5 remain consistent with the current week plan, architecture, and
accepted decisions.

## Completed work

- Added a versioned `1.0.0` documentation corpus with pinned official references for
  OpenAI 2.45.0, FastAPI 0.139.0, pydantic-settings 2.10.1, Modal 1.5.1, and ChromaDB
  1.1.1. The source manifest records library versions, document versions, URLs, local
  content paths, and SHA-256 content digests.
- Added deterministic Markdown section chunking and application-owned token-hash
  embeddings. The versioned ChromaDB index contains 12 chunks and is bundled at
  `rag/index/v1` for local and hosted backend use without an embedding-model download.
- Added index integrity checks for source digests, manifest hash, corpus version,
  embedding version, and stored chunk count. A stale, incomplete, or tampered corpus is
  rejected before retrieval.
- Added a bounded retrieval tool that returns up to five cited official-documentation
  excerpts. Only Athena planning and repair tasks and Hephaestus implementation tasks
  receive the tool. Janus and Argus do not receive it.
- Added per-run retrieval events to workflow state and API responses. Logged evidence
  includes the query and retrieved source metadata while excluding full chunk content
  from response serialization. Final reports receive the cited source IDs, titles, URLs,
  and retrieval queries.
- Added a separate five-case API evaluation catalog and runner for RAG and no-RAG model
  configurations. Reports record the exact model, corpus version, prompt version,
  configuration, response IDs, token usage, retrieved sources, and required or forbidden
  API terms.
- Added focused tests for corpus integrity, index construction, expected-source retrieval,
  tool source logging, per-run isolation, agent access boundaries, evaluation artifacts,
  and separate RAG versus no-RAG scoring.
- Declared the existing ChromaDB pin as a direct runtime dependency and extended CI type
  checking to include the `rag` package.
- End-of-phase review correction: added a narrow `.gitignore` exception for the bundled
  `rag/index/v1/chroma.sqlite3` database. The global `*.sqlite3` rule previously excluded
  the collection database, so a clean checkout or deployment would receive incomplete
  index artifacts even though retrieval worked in the original local checkout.
- End-of-phase review verification: added explicit coverage that the bundled Chroma
  database is present and nonempty, and confirmed FastAPI serializes retrieved source
  metadata without exposing full document chunks.

## Verification performed

- `ruff check .` passed.
- `ruff format --check .` passed with 40 files checked.
- `mypy backend benchmark rag tests` passed with 40 source files checked.
- `python -m pytest -q` passed with 58 tests; the two live Docker integration tests were
  skipped because the local Docker daemon was unavailable.
- The focused Day 5 suite passed with 11 tests.
- `python -m pip check` reported no broken requirements.
- `python -m rag.index` rebuilt the bundled version `1.0.0` index with 12 chunks.
- All five API evaluation prompts retrieved their expected source within the top three
  results.
- SQLite `PRAGMA integrity_check` returned `ok`; all 12 stored chunk IDs and documents
  matched the versioned, digest-verified corpus.
- Installed OpenAI, FastAPI, pydantic-settings, Modal, and ChromaDB versions matched the
  source manifest versions.
- `git check-ignore -q rag/index/v1/chroma.sqlite3` returned exit code 1, and
  `git ls-files --others --exclude-standard` listed the database as includable.
- FastAPI OpenAPI generation and response serialization confirmed the retrieval schema
  exposes source metadata but excludes full chunk content.
- `python -m rag.index --help` and `python -m rag.evaluation --help` passed.
- `uv pip compile requirements-dev.txt --python .venv/bin/python --output-file
  requirements.lock` completed. No package version changed; the lock now records ChromaDB
  as both direct and CrewAI-transitive.
- `git diff --check` passed.
- Focused secret scanning found no private keys or live OpenAI credentials in the Day 5
  diff; the only API-key match was the documented placeholder in `.env.example`.

## Known risks and deferred work

- The corpus is deliberately small and pinned. Library upgrades require a reviewed source
  snapshot, new digests, a corpus version bump, an index rebuild, and an evaluation rerun.
- Deterministic token-hash embeddings keep the bundled index reproducible and avoid model
  downloads, but provide weaker semantic matching than a dedicated embedding model. The
  five current API cases pass expected-source retrieval; broader retrieval quality has not
  been measured.
- The RAG and no-RAG evaluation harness is verified with deterministic test generators.
  A paid live model comparison remains intentionally unexecuted, so grounded answer quality
  and library hallucination rates are not yet measured.
- Live Docker execution was not reverified because the local daemon was unavailable. Modal
  remains verified against the installed SDK and contract-level fakes, not an authenticated
  cloud sandbox.
- Retrieval events are isolated per run and omit full document chunks from API serialization,
  but the number of tool calls is controlled by the agent workflow rather than a separate
  retrieval-call quota.
- FastAPI, CrewAI, Starlette, and OpenTelemetry emit upstream deprecation warnings during
  the test suite.

## Decisions added or changed

No architecture decisions changed. Day 5 implements D004 by keeping the five-case API RAG
evaluation separate from the 20-task algorithm benchmark. The hosted architecture continues
to use a prebuilt ChromaDB index bundled with the backend.

## Exact next task

Implement Day 6, Rebuild the frontend: replace Streamlit with Next.js and TypeScript; add
run submission, progress, attempts, logs, code, and RAG evidence views; add a dashboard for
precomputed benchmark results; and handle backend cold starts and interrupted runs clearly.
Do not begin Day 7 deployment work.

# Deployment

Day 7 deployment uses Vercel for the Next.js frontend, Render Free for the FastAPI
backend, and Modal for hosted sandbox execution. Do not run a public benchmark from the
hosted demo; benchmark execution remains local or CI-only.

## Backend on Render

Use `render.yaml` as the backend blueprint. Set these environment variables in Render:

```text
OPENAI_API_KEY=<secret>
OPENAI_MODEL_NAME=gpt-4o-mini
CORS_ORIGINS=["https://<vercel-project>.vercel.app"]
SANDBOX_BACKEND=modal
MODAL_SANDBOX_APP=digital-forge-sandbox
MAX_ACTIVE_RUNS=1
MAX_DAILY_MODEL_RUNS=20
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
RUN_TIMEOUT_SECONDS=300
```

The public backend is intentionally process-local: it allows one active run, applies a
small per-client rate limit, cancels at workflow boundaries after the configured timeout,
and stops accepting new model-backed runs after the daily process-local run budget is
exhausted.

Render must deploy from `mjp/revamp-digital-forge` until this branch is merged to `main`.
The repository pins Python in `runtime.txt`; do not use Render's default Python version.

## Frontend on Vercel

Deploy `frontend/` as the Vercel project root. Set:

```text
NEXT_PUBLIC_BACKEND_URL=https://<render-service>.onrender.com
```

The frontend build should run `npm ci` and `npm run build`.

## Modal Sandbox

Render must use `SANDBOX_BACKEND=modal` because Render Free is not a Docker host. The
Modal path builds the sandbox image from the same pinned offline capability set used by
Docker.

Authenticate Modal in the Render environment before live runs. Without Modal credentials,
the backend health check can pass but generated-code execution will fail as an
infrastructure configuration error.

## Smoke Tests

After deployment, verify:

```bash
curl -fsS https://<render-service>.onrender.com/health
curl -fsS https://<render-service>.onrender.com/benchmarks
```

Then open the Vercel URL and verify:

- Backend health shows connected after Render cold start.
- The benchmark dashboard loads tracked reports.
- A second submitted run while one is active returns `409`.
- Excess repeated submissions return `429`.
- One small paid live run reaches a terminal state through Modal before sharing the demo.

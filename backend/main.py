"""Single FastAPI and CLI entry point for The Digital Forge backend."""

import argparse
from collections.abc import Sequence
from threading import RLock
from time import monotonic
from uuid import UUID, uuid4

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from benchmark.models import BenchmarkReport

from .benchmarks import load_benchmark_reports
from .config import Settings, get_settings
from .models import RunRequest, RunResponse, RunSnapshot
from .run_manager import (
    ActiveRunLimitExceeded,
    CancellationCheck,
    DailyRunLimitExceeded,
    RunManager,
    Runner,
    RunnerFactory,
    UpdateCallback,
)


class RateLimiter:
    """Small process-local limiter for the public demo API."""

    def __init__(self, request_limit: int, window_seconds: float):
        self.request_limit = request_limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = RLock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        window_start = now - self.window_seconds
        with self._lock:
            timestamps = [
                timestamp
                for timestamp in self._requests.get(key, [])
                if timestamp >= window_start
            ]
            if len(timestamps) >= self.request_limit:
                self._requests[key] = timestamps
                return False
            timestamps.append(now)
            self._requests[key] = timestamps
        return True


def _default_runner(
    request: str,
    settings: Settings,
    run_id: UUID,
    on_update: UpdateCallback,
    is_cancel_requested: CancellationCheck,
) -> Runner:
    from .pipeline import DevelopmentCrew

    return DevelopmentCrew(
        request,
        settings,
        run_id=run_id,
        on_update=on_update,
        is_cancel_requested=is_cancel_requested,
    )


def create_app(
    settings: Settings | None = None,
    runner_factory: RunnerFactory | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    create_runner = runner_factory or _default_runner
    app = FastAPI(title="The Digital Forge", version="0.1.0")
    run_manager = RunManager(app_settings, create_runner)
    app.state.run_manager = run_manager
    app.state.rate_limiter = RateLimiter(
        app_settings.rate_limit_requests,
        app_settings.rate_limit_window_seconds,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    def enforce_rate_limit(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        if not app.state.rate_limiter.allow(client):
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    @app.post("/run", response_model=RunResponse)
    def run_pipeline(
        payload: RunRequest, _rate_limit: None = Depends(enforce_rate_limit)
    ) -> RunResponse:
        if len(payload.request) > app_settings.max_request_characters:
            raise HTTPException(status_code=413, detail="Request is too large.")
        try:
            run_manager.reserve_external_run()
        except ActiveRunLimitExceeded:
            raise HTTPException(
                status_code=409, detail="Another run is already active."
            ) from None
        except DailyRunLimitExceeded:
            raise HTTPException(
                status_code=429, detail="Daily model run limit exceeded."
            ) from None
        try:
            return create_runner(
                payload.request,
                app_settings,
                uuid4(),
                lambda _state: None,
                lambda: False,
            ).run()
        finally:
            run_manager.release_external_run()

    @app.post("/runs", response_model=RunSnapshot, status_code=202)
    def start_run(
        payload: RunRequest, _rate_limit: None = Depends(enforce_rate_limit)
    ) -> RunSnapshot:
        if len(payload.request) > app_settings.max_request_characters:
            raise HTTPException(status_code=413, detail="Request is too large.")
        try:
            return run_manager.start(payload.request)
        except ActiveRunLimitExceeded:
            raise HTTPException(
                status_code=409, detail="Another run is already active."
            ) from None
        except DailyRunLimitExceeded:
            raise HTTPException(
                status_code=429, detail="Daily model run limit exceeded."
            ) from None

    @app.get("/runs/{run_id}", response_model=RunSnapshot)
    def get_run(run_id: UUID) -> RunSnapshot:
        snapshot = run_manager.get(run_id)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        return snapshot

    @app.post("/runs/{run_id}/cancel", response_model=RunSnapshot)
    def cancel_run(run_id: UUID) -> RunSnapshot:
        snapshot = run_manager.cancel(run_id)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        return snapshot

    @app.get("/benchmarks", response_model=tuple[BenchmarkReport, ...])
    def benchmarks() -> tuple[BenchmarkReport, ...]:
        return load_benchmark_reports(app_settings.benchmark_results_path)

    return app


app = create_app()


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run The Digital Forge backend")
    parser.add_argument("request", nargs="?", help="Run one request from the CLI")
    args = parser.parse_args(argv)
    settings = get_settings()
    if args.request:
        from .pipeline import DevelopmentCrew

        print(DevelopmentCrew(args.request, settings).run().model_dump_json(indent=2))
    else:
        uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()

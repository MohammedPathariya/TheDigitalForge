"""Single FastAPI and CLI entry point for The Digital Forge backend."""

import argparse
from collections.abc import Sequence
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from benchmark.models import BenchmarkReport

from .benchmarks import load_benchmark_reports
from .config import Settings, get_settings
from .models import RunRequest, RunResponse, RunSnapshot
from .run_manager import (
    CancellationCheck,
    RunManager,
    Runner,
    RunnerFactory,
    UpdateCallback,
)


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

    @app.post("/run", response_model=RunResponse)
    def run_pipeline(payload: RunRequest) -> RunResponse:
        if len(payload.request) > app_settings.max_request_characters:
            raise HTTPException(status_code=413, detail="Request is too large.")
        return create_runner(
            payload.request,
            app_settings,
            uuid4(),
            lambda _state: None,
            lambda: False,
        ).run()

    @app.post("/runs", response_model=RunSnapshot, status_code=202)
    def start_run(payload: RunRequest) -> RunSnapshot:
        if len(payload.request) > app_settings.max_request_characters:
            raise HTTPException(status_code=413, detail="Request is too large.")
        return run_manager.start(payload.request)

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

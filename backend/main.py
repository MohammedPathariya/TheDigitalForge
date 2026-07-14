"""Single FastAPI and CLI entry point for The Digital Forge backend."""

import argparse
from collections.abc import Callable, Sequence
from typing import Protocol

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .models import RunRequest, RunResponse


class Runner(Protocol):
    def run(self) -> RunResponse: ...


RunnerFactory = Callable[[str, Settings], Runner]


def _default_runner(request: str, settings: Settings) -> Runner:
    from .pipeline import DevelopmentCrew

    return DevelopmentCrew(request, settings)


def create_app(
    settings: Settings | None = None,
    runner_factory: RunnerFactory | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    create_runner = runner_factory or _default_runner
    app = FastAPI(title="The Digital Forge", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/run", response_model=RunResponse)
    def run_pipeline(payload: RunRequest) -> RunResponse:
        if len(payload.request) > app_settings.max_request_characters:
            raise HTTPException(status_code=413, detail="Request is too large.")
        return create_runner(payload.request, app_settings).run()

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

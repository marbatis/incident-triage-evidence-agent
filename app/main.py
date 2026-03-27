from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.api.web import router as web_router
from app.config import get_settings
from app.db import init_db
from app.logging_config import configure_logging


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title="Incident Triage Evidence Agent",
        version="0.1.0",
        description="Deterministic incident triage with grounded evidence and optional LLM memo.",
        lifespan=app_lifespan,
    )

    static_path = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/health")
    def health() -> JSONResponse:
        mode = "openai" if settings.openai_api_key else "mock"
        return JSONResponse(
            {
                "status": "ok",
                "provider_mode": settings.provider_mode,
                "active_provider": mode,
            }
        )

    app.include_router(web_router)
    app.include_router(api_router)

    return app


app = create_app()

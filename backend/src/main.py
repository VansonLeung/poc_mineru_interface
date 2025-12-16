from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.observability.logging import setup_logging
from src.api import health, parse
from src.api.middleware import (
    RequestContextMiddleware,
    http_exception_handler,
    unhandled_exception_handler,
)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    app = FastAPI(title="Miner-U Parse API", version="1.0.0")

    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins_normalized,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=settings.cors_allow_credentials,
    )

    app.include_router(health.router)
    app.include_router(parse.router, prefix="/api/v1")
    return app


app = create_app()

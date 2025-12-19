from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.config.settings import get_settings
from src.observability.logging import setup_logging
from src.api import health, parse, jobs
from src.api.middleware import (
    RequestContextMiddleware,
    http_exception_handler,
    unhandled_exception_handler,
)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    app = FastAPI(title="Octopus Document Parser API", version="1.0.0")

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
    app.include_router(jobs.router, prefix="/api/v1")

    def custom_openapi():  # pragma: no cover - thin schema customization
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            description=app.description,
        )
        openapi_schema["servers"] = [{"url": settings.swagger_server_url}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    @app.get("/swagger.json", include_in_schema=False)
    def swagger_json() -> JSONResponse:  # pragma: no cover - simple pass-through
        # Cache the generated schema on the app to avoid regenerating
        if not getattr(app, "openapi_schema", None):
            app.openapi()
        return JSONResponse(app.openapi_schema)

    @app.get("/api-doc", include_in_schema=False)
    def api_doc() -> RedirectResponse:  # pragma: no cover - simple redirect
        return RedirectResponse(url="/docs")
    return app


app = create_app()

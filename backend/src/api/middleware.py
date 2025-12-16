from __future__ import annotations

import time
import uuid

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from src.observability.logging import get_request_id, set_request_id
from src.observability.metrics import metrics


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)
        request.state.start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - request.state.start_time) * 1000
        logger.info(f"{request.method} {request.url.path} completed in {duration_ms:.1f}ms")
        metrics.record(status_code=response.status_code, duration_ms=duration_ms)
        response.headers["X-Request-ID"] = request_id
        return response


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = get_request_id()
    duration_ms = (time.perf_counter() - getattr(request.state, "start_time", time.perf_counter())) * 1000
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    metrics.record(status_code=exc.status_code, duration_ms=duration_ms)
    response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "request_id": request_id})
    response.headers["X-Request-ID"] = request_id
    return response


async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: ANN401
    request_id = get_request_id()
    duration_ms = (time.perf_counter() - getattr(request.state, "start_time", time.perf_counter())) * 1000
    logger.exception("Unhandled error")
    metrics.record(status_code=500, duration_ms=duration_ms)
    response = JSONResponse(status_code=500, content={"detail": "Internal Server Error", "request_id": request_id})
    response.headers["X-Request-ID"] = request_id
    return response

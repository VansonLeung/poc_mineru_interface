from __future__ import annotations

import inspect
from typing import List, Optional, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status

from src.api.deps.auth import require_api_key
from src.config.settings import get_settings
from src.observability.logging import get_request_id
from src.services.async_job_service import AsyncJobService
from src.services.parse_service import ParseParams, ParseService

BACKEND_OPTIONS = [
    "pipeline",
    "vlm-transformers",
    "vlm-mlx-engine",
    "vlm-vllm-engine",
    "vlm-lmdeploy-engine",
    "vlm-http-client",
]

router = APIRouter()


def get_parse_service() -> ParseService:
    return ParseService(settings=get_settings())


def _resolve_parse_service() -> ParseService:
    # Look up the current provider at request time so tests can monkeypatch it.
    return get_parse_service()


def get_async_job_service() -> AsyncJobService:
    settings = get_settings()
    parse_service = ParseService(settings=settings)
    return AsyncJobService(parse_service=parse_service, settings=settings)


async def _call_parse(service: ParseService, files: List[UploadFile], params: ParseParams) -> tuple[list, list]:
    parse_fn = service.parse
    param_count = len(inspect.signature(parse_fn).parameters)
    result = parse_fn(files) if param_count == 1 else parse_fn(files, params)
    if inspect.isawaitable(result):
        result = await result
    if isinstance(result, dict):
        return result.get("outputs", []), result.get("errors", [])
    if isinstance(result, tuple) and len(result) == 2:
        return result  # type: ignore[return-value]
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid parse response")


@router.post("/parse")
async def parse_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Upload one or more PDF/image/DOC/DOCX files"),
    lang: str = Form("ch"),
    parse_method: str = Form("auto"),
    backend: Literal[
        "pipeline",
        "vlm-transformers",
        "vlm-mlx-engine",
        "vlm-vllm-engine",
        "vlm-lmdeploy-engine",
        "vlm-http-client",
    ] = Form("pipeline", description="Backend engine (options: " + ", ".join(BACKEND_OPTIONS) + ")"),
    start_page: Optional[int] = Form(None),
    end_page: Optional[int] = Form(None),
    formula_enable: bool = Form(True),
    table_enable: bool = Form(True),
    async_mode: bool = Form(False, description="Enable async processing (returns job_id immediately)"),
    callback_url: Optional[str] = Form(None, description="Webhook URL to notify when async job completes"),
    _auth: None = Depends(require_api_key),
    service: ParseService = Depends(_resolve_parse_service),
    async_service: AsyncJobService = Depends(get_async_job_service),
):
    """
    Parse PDF/image/DOC/DOCX files synchronously or asynchronously.

    **Sync mode** (default): Returns parsed outputs immediately after processing.

    **Async mode** (`async_mode=true`):
    - Returns job_id and status_url immediately
    - Poll status_url every 5 seconds until status is SUCCESS or FAILED
    - Optionally provide callback_url to receive webhook notification on completion
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")

    params = ParseParams(
        lang=lang,
        parse_method=parse_method,
        backend=backend,
        start_page=start_page,
        end_page=end_page,
        formula_enable=formula_enable,
        table_enable=table_enable,
    )

    # Async mode: submit job and return immediately
    if async_mode:
        job = await async_service.submit_job(
            files=files,
            params=params,
            callback_url=callback_url,
            background_tasks=background_tasks,
        )
        settings = get_settings()
        return {
            "job_id": job.job_id,
            "status": job.status,
            "status_url": f"{settings.swagger_server_url}/api/v1/jobs/{job.job_id}",
            "created_at": job.created_at.isoformat(),
            "request_id": job.request_id,
        }

    # Sync mode: process and return results immediately
    outputs, errors = await _call_parse(service, files, params)
    return {"outputs": outputs, "errors": errors, "request_id": get_request_id()}

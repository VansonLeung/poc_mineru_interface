from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.config.settings import Settings, get_settings
from src.models.job import Job, get_job_store
from src.services.async_job_service import AsyncJobService
from src.services.parse_service import ParseService

router = APIRouter()


def get_async_job_service() -> AsyncJobService:
    settings = get_settings()
    parse_service = ParseService(settings=settings)
    return AsyncJobService(parse_service=parse_service, settings=settings)


@router.get("/jobs/{job_id}", response_model=Job, summary="Get job status")
async def get_job_status(
    job_id: str,
    service: AsyncJobService = Depends(get_async_job_service),
):
    """
    Retrieve the status of an async parse job.

    - **job_id**: The unique identifier of the job
    - Returns job status: PENDING, PROCESSING, SUCCESS, or FAILED
    - Completed jobs include outputs (SUCCESS) or errors (FAILED)
    """
    return await service.get_job_status(job_id)

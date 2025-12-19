from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from loguru import logger

from src.config.settings import Settings
from src.models.job import Job, JobStatus, get_job_store
from src.observability.logging import get_request_id
from src.services.parse_service import ParseParams, ParseService
from src.services.webhook_service import WebhookService


class AsyncJobService:
    """Manage async parse jobs with background execution."""

    def __init__(
        self,
        parse_service: ParseService,
        settings: Settings,
        webhook_service: WebhookService | None = None,
    ) -> None:
        self.parse_service = parse_service
        self.settings = settings
        self.job_store = get_job_store()
        self.webhook_service = webhook_service or WebhookService()

    async def submit_job(
        self,
        files: List[UploadFile],
        params: ParseParams,
        callback_url: str | None,
        background_tasks: BackgroundTasks,
    ) -> Job:
        """Submit a new async parse job."""
        # Check concurrent job limit
        active_count = await self.job_store.count_active()
        if active_count >= self.settings.max_concurrent_jobs:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Too many concurrent jobs ({active_count}/{self.settings.max_concurrent_jobs})",
            )

        # Create job record
        job_id = uuid.uuid4().hex
        job = Job(
            job_id=job_id,
            status=JobStatus.PENDING,
            request_id=get_request_id(),
            callback_url=callback_url,
        )
        await self.job_store.create(job)

        # Read files into memory before background task
        file_bytes = await self.parse_service._read_files(files)

        # Schedule background execution
        background_tasks.add_task(
            self._execute_job,
            job_id,
            file_bytes,
            params,
        )

        logger.opt(colors=True).info(
            "<cyan>async job submitted</cyan> job_id={job_id} files={files}",
            job_id=job_id,
            files=[name for name, _ in file_bytes],
        )
        return job

    async def _execute_job(
        self,
        job_id: str,
        file_bytes: list[tuple[str, bytes]],
        params: ParseParams,
    ) -> None:
        """Execute parse job in background."""
        job = await self.job_store.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found during execution")
            return

        # Mark as processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        await self.job_store.update(job)

        try:
            # Convert bytes back to normalized format
            normalized_files = self.parse_service._normalize_inputs(file_bytes)

            # Execute parse (same logic as sync mode)
            adapter = self.parse_service._get_adapter(job_id)
            parse_kwargs = {
                "lang": params.lang,
                "backend": params.backend,
                "parse_method": params.parse_method,
                "server_url": params.server_url,
                "start_page": params.start_page or 0,
                "end_page": params.end_page,
                "formula_enable": params.formula_enable,
                "table_enable": params.table_enable,
            }

            if params.backend == "vlm-mlx-engine":
                async with self.parse_service._get_mlx_lock():
                    mineru_outputs = await asyncio.to_thread(
                        adapter.parse_from_bytes,
                        normalized_files,
                        **parse_kwargs,
                    )
            else:
                mineru_outputs = await asyncio.to_thread(
                    adapter.parse_from_bytes,
                    normalized_files,
                    **parse_kwargs,
                )

            # Build outputs
            builder = self.parse_service._get_output_builder()
            outputs = builder.build(job_id=job_id, mineru_outputs=mineru_outputs)

            # Mark as success
            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.now(timezone.utc)
            job.outputs = outputs
            job.errors = []
            await self.job_store.update(job)

            logger.opt(colors=True).info(
                "<green>async job completed</green> job_id={job_id} outputs={count}",
                job_id=job_id,
                count=len(outputs),
            )

        except HTTPException as exc:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.errors = [{"detail": exc.detail, "status_code": exc.status_code}]
            await self.job_store.update(job)
            logger.warning(f"Async job {job_id} failed: {exc.detail}")

        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.errors = [{"detail": str(exc), "type": type(exc).__name__}]
            await self.job_store.update(job)
            logger.exception(f"Async job {job_id} failed with exception")

        # Send webhook if configured
        if job.callback_url:
            await self._send_webhook(job)

        # Cleanup old jobs
        self.parse_service.storage.cleanup_if_needed()

    async def _send_webhook(self, job: Job) -> None:
        """Send webhook notification for completed job."""
        if not job.callback_url:
            return

        payload = {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "outputs": job.outputs,
            "errors": job.errors,
            "request_id": job.request_id,
        }
        await self.webhook_service.notify(job.callback_url, payload)

    async def get_job_status(self, job_id: str) -> Job:
        """Retrieve job status."""
        job = await self.job_store.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )
        return job

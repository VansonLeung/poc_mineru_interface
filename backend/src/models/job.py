from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Job(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    request_id: Optional[str] = None
    callback_url: Optional[str] = None

    class Config:
        use_enum_values = True


class JobStore:
    """In-memory job storage with TTL-based cleanup."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create(self, job: Job) -> Job:
        async with self._lock:
            self._jobs[job.job_id] = job
        return job

    async def get(self, job_id: str) -> Optional[Job]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update(self, job: Job) -> Job:
        async with self._lock:
            self._jobs[job.job_id] = job
        return job

    async def delete(self, job_id: str) -> bool:
        async with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    async def list_expired(self, ttl_hours: int) -> List[str]:
        """Return list of job IDs that are older than ttl_hours and completed."""
        cutoff = datetime.now(timezone.utc).timestamp() - (ttl_hours * 3600)
        expired_ids = []
        async with self._lock:
            for job_id, job in self._jobs.items():
                if job.completed_at and job.completed_at.timestamp() < cutoff:
                    expired_ids.append(job_id)
        return expired_ids

    async def cleanup_expired(self, ttl_hours: int) -> int:
        """Remove expired completed jobs and return count removed."""
        expired = await self.list_expired(ttl_hours)
        for job_id in expired:
            await self.delete(job_id)
        return len(expired)

    async def count_active(self) -> int:
        """Count jobs that are PENDING or PROCESSING."""
        async with self._lock:
            return sum(
                1
                for job in self._jobs.values()
                if job.status in {JobStatus.PENDING, JobStatus.PROCESSING}
            )


# Global singleton instance
_job_store: Optional[JobStore] = None


def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.config.settings import get_settings


class StorageManager:
    """File-system backed temp storage with TTL-based cleanup."""

    def __init__(self, base_path: str | Path | None = None, ttl_hours: int | None = None) -> None:
        settings = get_settings()
        self.base_path = Path(base_path or settings.output_base_path)
        self.ttl_hours = ttl_hours if ttl_hours is not None else settings.output_ttl_hours
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._last_cleanup: datetime | None = None

    def job_dir(self, job_id: str) -> Path:
        path = self.base_path / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def expiry_at(self, now: datetime | None = None) -> datetime:
        now = now or datetime.now(timezone.utc)
        return now + timedelta(hours=self.ttl_hours)

    def write_text(self, job_id: str, filename: str, content: str) -> Path:
        path = self.job_dir(job_id) / filename
        path.write_text(content, encoding="utf-8")
        return path

    def write_bytes(self, job_id: str, filename: str, data: bytes) -> Path:
        path = self.job_dir(job_id) / filename
        path.write_bytes(data)
        return path

    def write_json(self, job_id: str, filename: str, payload: Any) -> Path:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        return self.write_text(job_id, filename, text)

    def cleanup_expired(self, now: datetime | None = None) -> list[Path]:
        now = now or datetime.now(timezone.utc)
        removed: list[Path] = []
        cutoff = now - timedelta(hours=self.ttl_hours)
        for child in self.base_path.iterdir():
            if not child.is_dir():
                continue
            mtime = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
                removed.append(child)
        return removed

    def cleanup_if_needed(self, now: datetime | None = None, interval_minutes: int = 60) -> list[Path]:
        now = now or datetime.now(timezone.utc)
        if self._last_cleanup and (now - self._last_cleanup) < timedelta(minutes=interval_minutes):
            return []
        self._last_cleanup = now
        return self.cleanup_expired(now=now)

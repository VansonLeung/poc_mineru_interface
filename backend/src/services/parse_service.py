from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import List, Tuple

from fastapi import HTTPException, UploadFile, status
from loguru import logger

from src.api.validators import validate_files, validate_pages
from src.config.settings import Settings, get_settings
from src.observability.logging import get_request_id
from src.services.mineru_adapter import MineruAdapter, MineruOutputPaths, MineruUnavailableError
from src.services.output_builder import OutputBuilder
from src.services.storage import StorageManager


@dataclass
class ParseParams:
    lang: str = "ch"
    parse_method: str = "auto"
    backend: str = "pipeline"
    start_page: int | None = None
    end_page: int | None = None
    formula_enable: bool = True
    table_enable: bool = True
    server_url: str | None = None


class ParseService:
    def __init__(self, settings: Settings | None = None, storage: StorageManager | None = None) -> None:
        self.settings = settings or get_settings()
        self.storage = storage or StorageManager(
            base_path=self.settings.output_base_path,
            ttl_hours=self.settings.output_ttl_hours,
        )

    async def parse(self, files: List[UploadFile], params: ParseParams) -> tuple[list[dict], list[dict]]:
        validate_files(files, self.settings)
        validate_pages(params.start_page, params.end_page, self.settings)

        file_bytes = await self._read_files(files)
        job_id = uuid.uuid4().hex
        adapter = MineruAdapter(output_dir=self.storage.job_dir(job_id))

        try:
            mineru_outputs = await asyncio.to_thread(
                adapter.parse_from_bytes,
                file_bytes,
                lang=params.lang,
                backend=params.backend,
                parse_method=params.parse_method,
                server_url=params.server_url,
                start_page=params.start_page or 0,
                end_page=params.end_page,
                formula_enable=params.formula_enable,
                table_enable=params.table_enable,
            )
        except MineruUnavailableError as exc:
            logger.warning(f"Miner-U dependencies missing: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Miner-U not installed (install torch/mineru extras)",
            ) from exc
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Miner-U parse failed")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Parse failed") from exc

        builder = OutputBuilder(storage=self.storage)
        outputs = builder.build(job_id=job_id, mineru_outputs=mineru_outputs)
        self.storage.cleanup_if_needed()
        return outputs, []

    async def _read_files(self, files: List[UploadFile]) -> list[Tuple[str, bytes]]:
        results: list[Tuple[str, bytes]] = []
        for upload in files:
            data = await upload.read()
            if len(data) > self.settings.max_file_bytes:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
            results.append((upload.filename, data))
        return results

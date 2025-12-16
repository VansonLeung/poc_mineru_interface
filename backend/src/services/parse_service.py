from __future__ import annotations

import asyncio
import io
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
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
        normalized_files = self._normalize_inputs(file_bytes)
        logger.opt(colors=True).info(
            "<cyan>parse request</cyan> lang={lang} backend={backend} parse_method={method} files={files}",
            lang=params.lang,
            backend=params.backend,
            method=params.parse_method,
            files=[name for name, _ in normalized_files],
        )
        job_id = uuid.uuid4().hex
        adapter = MineruAdapter(output_dir=self.storage.job_dir(job_id))

        try:
            mineru_outputs = await asyncio.to_thread(
                adapter.parse_from_bytes,
                normalized_files,
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
            logger.warning(f"Miner-U unavailable: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Miner-U parse failed")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Parse failed") from exc

        builder = OutputBuilder(storage=self.storage)
        outputs = builder.build(job_id=job_id, mineru_outputs=mineru_outputs)
        logger.opt(colors=True).info(
            "<green>parse success</green> job_id={job} outputs={outputs} errors={errors}",
            job=job_id,
            outputs=[out.get("filename") for out in outputs],
            errors=[],
        )
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

    def _normalize_inputs(self, files: list[Tuple[str, bytes]]) -> list[Tuple[str, bytes]]:
        """Convert doc/docx to PDF bytes so Miner-U can parse, keep other formats as-is."""
        normalized: list[Tuple[str, bytes]] = []
        for name, data in files:
            suffix = (name or "").rsplit(".", 1)[-1].lower()
            stem = Path(name).stem if name else "file"
            if suffix in {"doc", "docx"}:
                pdf_bytes = self._convert_doc_to_pdf(name, data)
                normalized.append((f"{stem}.pdf", pdf_bytes))
            elif suffix in {"png", "jpg", "jpeg", "bmp", "gif", "webp", "jp2"}:
                pdf_bytes = self._convert_image_to_pdf(name, data)
                normalized.append((f"{stem}.pdf", pdf_bytes))
            else:
                normalized.append((name, data))
        return normalized

    def _convert_doc_to_pdf(self, filename: str, data: bytes) -> bytes:
        docx_error: Exception | None = None

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / filename
            pdf_path = Path(tmpdir) / (Path(filename).stem + ".pdf")
            src_path.write_bytes(data)

            try:
                from docx2pdf import convert

                convert(str(src_path), str(pdf_path))
            except Exception as exc:  # noqa: BLE001
                docx_error = exc
                logger.warning("DOCX to PDF via docx2pdf failed: %s", exc)
            if pdf_path.exists():
                return pdf_path.read_bytes()

            # Fallback to LibreOffice/soffice if available
            soffice_bin = shutil.which("soffice") or shutil.which("libreoffice")
            if soffice_bin:
                try:
                    subprocess.run(
                        [soffice_bin, "--headless", "--convert-to", "pdf", str(src_path), "--outdir", tmpdir],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                except subprocess.CalledProcessError as exc:  # noqa: PERF203
                    logger.warning("DOCX to PDF via LibreOffice failed: %s", exc)
                if pdf_path.exists():
                    return pdf_path.read_bytes()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to convert DOCX to PDF (requires Word on macOS or LibreOffice)",
        ) from docx_error

    def _convert_image_to_pdf(self, filename: str, data: bytes) -> bytes:
        try:
            from PIL import Image
        except ImportError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Image support unavailable") from exc

        try:
            with Image.open(io.BytesIO(data)) as img:
                rgb = img.convert("RGB")
                with tempfile.TemporaryDirectory() as tmpdir:
                    pdf_path = Path(tmpdir) / (Path(filename).stem + ".pdf")
                    rgb.save(pdf_path, format="PDF")
                    return pdf_path.read_bytes()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Image to PDF conversion failed: %s", exc)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to convert image to PDF") from exc

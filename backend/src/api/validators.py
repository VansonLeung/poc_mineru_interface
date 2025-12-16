from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException, UploadFile, status

from src.config.settings import Settings

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jp2",
    "image/webp",
    "image/gif",
    "image/bmp",
}
ALLOWED_EXTENSIONS = {"pdf", "png", "jpeg", "jpg", "jp2", "webp", "gif", "bmp"}


def _is_allowed(upload: UploadFile) -> bool:
    if upload.content_type in ALLOWED_MIME_TYPES:
        return True
    suffix = (upload.filename or "").split(".")[-1].lower()
    return suffix in ALLOWED_EXTENSIONS


def validate_files(files: Iterable[UploadFile], settings: Settings) -> None:
    if files is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")

    file_list = list(files)
    if not file_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")
    if len(file_list) > settings.max_files:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too many files")

    for upload in file_list:
        if not _is_allowed(upload):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")


def validate_pages(start_page: int | None, end_page: int | None, settings: Settings) -> None:
    if start_page is not None and start_page < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_page must be >= 0")
    if end_page is not None and end_page < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_page must be >= 0")
    if start_page is not None and end_page is not None and end_page < start_page:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_page must be >= start_page")
    if start_page is not None and end_page is not None:
        if (end_page - start_page + 1) > settings.max_pages:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too many pages requested")
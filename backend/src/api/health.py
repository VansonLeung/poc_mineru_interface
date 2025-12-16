from datetime import datetime, timezone

from fastapi import APIRouter

from src.config.settings import get_settings
from src.observability.metrics import metrics

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    mineru_ready = True
    return {
        "status": "ok",
        "mineru_ready": mineru_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "limits": {
            "max_file_bytes": settings.max_file_bytes,
            "max_pages": settings.max_pages,
            "max_files": settings.max_files,
        },
        "metrics": metrics.snapshot(),
    }

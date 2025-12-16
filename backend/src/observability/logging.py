import sys
from contextvars import ContextVar
from typing import Optional

from loguru import logger

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def _patch_request_id(record: dict) -> dict:
    """Ensure every log record carries a request_id for format usage."""
    record["extra"].setdefault("request_id", get_request_id())
    return record


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru with request_id in the format string."""
    logger.remove()
    logger.configure(
        extra={"request_id": "-"},
        patcher=_patch_request_id,
        handlers=[
            {
                "sink": sys.stdout,
                "level": level,
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {extra[request_id]} | {message}",
                "backtrace": True,
                "diagnose": False,
            }
        ],
    )


def set_request_id(request_id: Optional[str]) -> None:
    _request_id_ctx.set(request_id or "-")


def get_request_id() -> str:
    return _request_id_ctx.get("-")

from fastapi import Header, HTTPException, status

from src.config.settings import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    settings = get_settings()
    if not settings.api_key_required:
        return
    if not x_api_key or x_api_key != settings.api_key_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

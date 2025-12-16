from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cors_allow_origins: List[str] | str = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = False

    max_file_bytes: int = 50 * 1024 * 1024
    max_pages: int = 50
    max_files: int = 5

    output_base_path: str = "/tmp/mineru-outputs"
    output_ttl_hours: int = 24

    mineru_model_source: str = "local"

    api_key_required: bool = False
    api_key_value: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _coerce_cors_allow_origins(cls, value: object) -> list[str]:
        if value is None:
            return ["*"]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped == "*":
                return ["*"]
            parts = [item.strip() for item in stripped.split(",") if item.strip()]
            return parts or ["*"]
        if isinstance(value, (list, tuple)):
            return list(value)
        raise ValueError("cors_allow_origins must be a string or list of strings")

    @property
    def cors_allow_origins_normalized(self) -> List[str]:
        origins = []
        for origin in self.cors_allow_origins:
            if origin == "*":
                return ["*"]
            parts = [item.strip() for item in origin.split(",") if item.strip()]
            origins.extend(parts if parts else [origin])
        return origins or ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

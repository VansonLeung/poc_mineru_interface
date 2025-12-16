# Security Notes

- Secrets: configure via environment variables (`API_KEY_VALUE`, `API_KEY_REQUIRED`, Miner-U model source). Do not commit secrets.
- CORS: allow-all with credentials=false per requirements; tighten for production by setting `CORS_ALLOW_ORIGINS`.
- Storage: temp outputs under `OUTPUT_BASE_PATH` with TTL cleanup; run `StorageManager.cleanup_expired` periodically (built-in on parse path).
- Dependency hygiene: run `uv run pip list --outdated` and `npm audit` regularly; CI runs lint/tests with coverage.
- Authentication: optional API key checked via `X-API-Key` header when enabled.
- Logging: request IDs included; avoid logging raw file contents.

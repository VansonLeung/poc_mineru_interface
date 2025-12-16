# Research (Phase 0)

## Parsing workflow
- **Decision**: Use Miner-U 2.6.8 pipeline backend with sync responses and per-file page/size limits (<=50MB or <=50 pages).
- **Rationale**: Matches spec requirement for synchronous returns; pipeline mode is most general and aligns with provided reference script.
- **Alternatives considered**: VLM backends (faster on some hardware) rejected for now to keep deterministic PoC and avoid GPU dependency.

## API surface
- **Decision**: Single versioned endpoint `POST /api/v1/parse` (multipart) returning Markdown/JSON payloads or download URLs in the same response.
- **Rationale**: Satisfies synchronous requirement and Dify tool use; versioned path supports future additive changes.
- **Alternatives considered**: Async job polling endpoint rejected per clarification; streaming chunked responses deferred due to added complexity.

## Storage & retention
- **Decision**: Local filesystem temp storage per job with time-limited cleanup (e.g., 24h) and optional immediate deletion flag.
- **Rationale**: Minimal ops overhead for PoC; avoids external dependencies.
- **Alternatives considered**: Object storage (S3/minio) deferred until persistence/scale requirements emerge.

## CORS and access
- **Decision**: Allow-all origins with `credentials=false`; optional API key header toggle for deployments needing control.
- **Rationale**: Directly aligns with user requirement while leaving a simple guardrail option.
- **Alternatives considered**: Origin allowlist or OAuth2 rejected for initial delivery; can be added later without breaking API v1.

## Testing approach
- **Decision**: Contract tests (httpx/pytest) for `POST /api/v1/parse`, integration tests invoking Miner-U on sample PDF and image, unit tests for validation and limits, optional Playwright e2e for UI upload→download.
- **Rationale**: Covers synchronous behavior, error paths, and regression for parsing outputs; supports >=85% coverage target.
- **Alternatives considered**: Skipping UI e2e rejected; mocking Miner-U for integration rejected (need real outputs to guard against drift).

## Observability
- **Decision**: Structured logging (request_id, file names, durations, error codes) plus basic metrics (request rate, success/fail counts, latency) and `/health` readiness.
- **Rationale**: Meets constitution observability gate and supports triage for failed parses.
- **Alternatives considered**: Tracing deferred for PoC to reduce setup overhead.

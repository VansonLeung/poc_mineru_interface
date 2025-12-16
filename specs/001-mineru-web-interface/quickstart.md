# Quickstart

## Prereqs
- Python 3.11
- uv (or pip) and virtualenv
- Node 18+ (for frontend if used)
- Miner-U 2.6.8 model assets accessible (see `_references/mineru_demo.py`); set `MINERU_MODEL_SOURCE` if needed

## Backend setup
```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install fastapi uvicorn loguru httpx pytest pytest-asyncio pydantic mineru==2.6.8
uvicorn src.main:app --reload
```

## Frontend setup (if using SPA)
```bash
cd frontend
npm install
npm run dev
```

## API usage
```bash
curl -X POST http://localhost:8000/api/v1/parse \
  -F "files=@/path/to/doc.pdf" \
  -F "parse_method=auto" \
  -F "backend=pipeline"
```
- Response includes Markdown/JSON payloads or download URLs; synchronous only.

## Health check
```bash
curl http://localhost:8000/health
```

## Tests
```bash
cd backend
pytest
# Optional UI e2e (Playwright)
cd ../frontend
npm run test:e2e
```

## Cleanup
- Temp outputs stored on local disk per job; configure expiry (e.g., 24h) and ensure periodic cleanup.

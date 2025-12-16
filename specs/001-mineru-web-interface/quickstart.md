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
uv pip install .[dev]
uvicorn src.main:app --reload
```

## Frontend setup (SPA)
```bash
cd frontend
npm install
npm run dev
```

## Environment
- Copy `backend/.env.example` to `backend/.env` and adjust limits or API key (`API_KEY_REQUIRED`, `API_KEY_VALUE`).
- Default CORS is allow-all, credentials=false.

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
# Backend
cd backend
uv run pytest --cov=src --cov-report=term-missing

# Frontend unit
cd ../frontend
npm test -- --coverage

# Frontend e2e (needs dev server)
npm run test:e2e
```

## Cleanup
- Temp outputs stored on local disk per job; configure expiry (e.g., 24h) and ensure periodic cleanup.

# Miner-U Web Interface

Synchronous Miner-U 2.6.8 parse API with a React/Vite web UI.

## Getting Started
- Backend: see `backend/pyproject.toml` and run `uv pip install .[dev]` or `uv pip install .\[dev\]` then `uvicorn src.main:app  --host 0.0.0.0 --port 19833 --reload`.
- Frontend: `cd frontend && npm install && npm run dev`.
- Env: copy `backend/.env.example` to `.env` and set limits/API key as needed.

## Docs
- Spec/plan/tasks: `specs/001-mineru-web-interface/`
- Quickstart: `specs/001-mineru-web-interface/quickstart.md`
- API contract: `specs/001-mineru-web-interface/contracts/openapi.yaml`
- Dify tool notes: `backend/docs/dify-tool.md`
- Runbook: `docs/runbooks/mineru-parse.md`

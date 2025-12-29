# Miner-U Web Interface

Miner-U 2.6.8 parse API with async/sync modes and a React/Vite web UI.

## Features

- ✅ **Sync Mode**: Immediate response with parsed results (traditional blocking API)
- ✅ **Async Mode**: Background job processing with status polling (non-blocking API)
- ✅ **Job Management**: Track job status, query results, webhook callbacks
- ✅ **Web UI**: Upload files, toggle async mode, real-time status updates
- ✅ **Multiple Backends**: Pipeline, VLM (Transformers, MLX, vLLM, LMDeploy), HTTP client
- ✅ **Format Support**: PDF, images (PNG/JPG/JPEG/JP2/WebP/GIF/BMP), DOC/DOCX

## Getting Started

### Backend Setup
```bash
cd backend
uv pip install .[dev]  # or uv pip install .\[dev\] on some shells
uvicorn src.main:app --host 0.0.0.0 --port 28109 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Configuration
Copy `backend/.env.example` to `backend/.env` and configure:
```bash
# CORS origins (comma-separated or "*")
CORS_ALLOW_ORIGINS=*

# File upload limits
MAX_FILE_BYTES=52428800  # 50MB
MAX_FILES=5
MAX_PAGES=50

# Async job limits
MAX_CONCURRENT_JOBS=10

# Output storage
OUTPUT_BASE_PATH=/tmp/mineru-outputs
OUTPUT_TTL_HOURS=24

# API key (optional)
API_KEY_REQUIRED=false
API_KEY_VALUE=your-secret-key
```

## API Usage

### Sync Mode (Default)

**Request:**
```bash
curl -X POST http://localhost:28109/api/v1/parse \
  -F "files=@document.pdf" \
  -F "parse_method=auto" \
  -F "backend=pipeline"
```

**Response:** Immediate results
```json
{
  "outputs": [
    {
      "filename": "document.pdf",
      "markdown": "# Parsed content...",
      "content_list_json": {...},
      "storage_expiry": "2025-12-20T10:00:00Z"
    }
  ],
  "request_id": "abc123..."
}
```

### Async Mode

**1. Submit Job:**
```bash
curl -X POST http://localhost:28109/api/v1/parse \
  -F "files=@document.pdf" \
  -F "async_mode=true" \
  -F "backend=pipeline" \
  -F "callback_url=https://your-webhook.com/callback"  # optional
```

**Response:** Job ID returned immediately
```json
{
  "job_id": "abc123...",
  "status": "PENDING",
  "status_url": "/api/v1/jobs/abc123...",
  "created_at": "2025-12-19T10:00:00Z"
}
```

**2. Poll Job Status:**
```bash
curl http://localhost:28109/api/v1/jobs/abc123...
```

**Response:** Job status and results (when complete)
```json
{
  "job_id": "abc123...",
  "status": "SUCCESS",  // PENDING | PROCESSING | SUCCESS | FAILED
  "created_at": "2025-12-19T10:00:00Z",
  "completed_at": "2025-12-19T10:00:35Z",
  "outputs": [
    {
      "filename": "document.pdf",
      "markdown": "# Parsed content...",
      "content_list_json": {...}
    }
  ]
}
```

**Polling Recommendation:** Poll every 5 seconds with max 120 attempts (10 minutes timeout).

### Webhook Callbacks

When `callback_url` is provided, a POST request is sent on job completion:

**Webhook Payload (SUCCESS):**
```json
{
  "job_id": "abc123...",
  "status": "SUCCESS",
  "created_at": "2025-12-19T10:00:00Z",
  "completed_at": "2025-12-19T10:00:35Z",
  "outputs": [...]
}
```

**Webhook Payload (FAILED):**
```json
{
  "job_id": "abc123...",
  "status": "FAILED",
  "created_at": "2025-12-19T10:00:00Z",
  "completed_at": "2025-12-19T10:00:45Z",
  "error": "Error message..."
}
```

## Web UI

Open http://localhost:28108 (or auto-assigned port) and:

1. **Sync Mode** (default): Upload → Wait for processing → View results
2. **Async Mode** (checkbox): Upload → Get job ID → Watch status updates → View results

**Async UI Features:**
- Real-time job status (PENDING → PROCESSING → SUCCESS)
- Job ID and timestamps display
- Progress indicators with emojis (⏳ ⚙️)
- Automatic polling every 5 seconds
- Same result viewer as sync mode

## Documentation

### Core Docs
- **API Contract**: `specs/001-mineru-web-interface/contracts/openapi.yaml`
- **Quickstart**: `specs/001-mineru-web-interface/quickstart.md`
- **Spec/Plan/Tasks**: `specs/001-mineru-web-interface/`

### Async Mode Docs
- **Backend Implementation**: `ASYNC_MODE_SUMMARY.md`
- **API Documentation**: `backend/docs/async-mode.md`
- **Frontend Implementation**: `FRONTEND_ASYNC_UPDATE.md`
- **Manual Test Guide**: `FRONTEND_MANUAL_TEST.md`

### Additional Docs
- **Dify Tool Integration**: `backend/docs/dify-tool.md`
- **Runbook**: `docs/runbooks/mineru-parse.md`
- **CORS Fix**: `CORS_FIX.md`

## Architecture

```
┌─────────────┐      HTTP/HTTPS      ┌──────────┐
│   Browser   │ ←──────────────────→ │  Nginx   │
│  (React UI) │                      │  Proxy   │
└─────────────┘                      └──────────┘
                                           │
                                           ↓
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                     │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Sync Mode  │  │  Async Mode  │  │   Job Store │ │
│  │  (Parse)   │  │ (Background) │  │ (In-Memory) │ │
│  └────────────┘  └──────────────┘  └─────────────┘ │
│         │                │                           │
│         └────────────────┴─────────────┐             │
│                                        ↓             │
│                              ┌──────────────────┐   │
│                              │  Miner-U Engine  │   │
│                              │  (PDF/Image OCR) │   │
│                              └──────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Backend Options

- **`pipeline`**: Fast, CPU-based (default)
- **`vlm-transformers`**: GPU-accelerated vision-language model
- **`vlm-mlx-engine`**: Apple Silicon optimized (M1/M2/M3)
- **`vlm-vllm-engine`**: vLLM inference server
- **`vlm-lmdeploy-engine`**: LMDeploy inference server
- **`vlm-http-client`**: External HTTP API client

## Testing

```bash
# Backend unit tests
cd backend
pytest

# Backend integration tests
pytest tests/integration/

# Frontend unit tests
cd frontend
npm test

# Frontend E2E tests
npm run test:e2e

# Build verification
npm run build
```

## Deployment

### Backend
```bash
cd backend
uv pip install .
uvicorn src.main:app --host 0.0.0.0 --port 28109 --workers 4
```

### Frontend
```bash
cd frontend
npm run build
# Serve dist/ with nginx or static file server
```

### Nginx Configuration
See `CORS_FIX.md` for proper Nginx + FastAPI CORS setup.

**Key points:**
- Let FastAPI handle CORS (via `CORSMiddleware`)
- Do NOT add CORS headers in Nginx (causes duplicates)
- Configure timeouts for large files: `proxy_read_timeout 2400s`
- Configure body size: `client_max_body_size 500M`

## Troubleshooting

### CORS Errors
- ✅ Backend handles CORS via `CORSMiddleware`
- ❌ Do NOT add `Access-Control-*` headers in Nginx
- See `CORS_FIX.md` for details

### Job Not Processing
- Check backend logs: `uvicorn src.main:app --reload --log-level debug`
- Verify job status: `curl http://localhost:28109/api/v1/jobs/{job_id}`
- Check concurrent job limit: `MAX_CONCURRENT_JOBS` in `.env`

### Large File Upload Fails
- Increase `MAX_FILE_BYTES` in backend `.env`
- Increase `client_max_body_size` in Nginx config
- Check disk space in `OUTPUT_BASE_PATH`

### Async Job Timeout
- Increase polling `maxAttempts` in frontend code
- Check backend processing time (MLX backend ~30s, pipeline ~5s)
- Verify backend isn't overloaded (check CPU/memory)

## License

See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

## Support

- Issues: GitHub Issues
- Docs: See documentation links above
- API: OpenAPI spec at `/docs` when backend is running

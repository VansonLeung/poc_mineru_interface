# Async Mode Implementation Summary

## What Was Implemented

### 1. Core Components

#### Job Management (`src/models/job.py`)
- `JobStatus` enum: PENDING, PROCESSING, SUCCESS, FAILED
- `Job` model: Complete job state with timestamps, outputs, errors
- `JobStore`: In-memory storage with TTL-based cleanup
- Thread-safe operations with asyncio locks

#### Configuration (`src/config/settings.py`)
- `max_concurrent_jobs`: Limit concurrent async jobs (default: 10)

#### Services
- **AsyncJobService** (`src/services/async_job_service.py`):
  - Submit jobs with concurrency control
  - Background execution using FastAPI BackgroundTasks
  - Job status tracking with state transitions
  - MLX backend serialization (reuses existing lock)
  
- **WebhookService** (`src/services/webhook_service.py`):
  - Fire-and-forget HTTP POST notifications
  - Timeout handling (30s default)
  - Error logging without retry

#### API Endpoints
- **POST /api/v1/parse** (updated):
  - New parameter: `async_mode` (bool, default: false)
  - New parameter: `callback_url` (str, optional)
  - Sync mode: Returns outputs immediately (backward compatible)
  - Async mode: Returns job_id and status_url immediately
  
- **GET /api/v1/jobs/{job_id}** (new):
  - Query job status and results
  - Returns full job state including outputs when completed

### 2. Features Delivered

✅ **Async mode toggle via parameter**
- Backward compatible (default: sync mode)
- Clean API design with boolean flag

✅ **Immediate response on job submission**
- Returns job_id, status, status_url, created_at, request_id
- Client can poll status_url

✅ **Job status query endpoint**
- Four states: PENDING → PROCESSING → SUCCESS/FAILED
- Includes outputs (SUCCESS) or errors (FAILED)
- Timestamps: created_at, started_at, completed_at

✅ **Webhook/callback support**
- Optional callback_url parameter
- Fire-and-forget POST with full job payload
- Logged but non-blocking

✅ **Concurrent job limiting**
- Configurable max (default: 10)
- Returns 503 when limit exceeded
- Count only PENDING/PROCESSING jobs

✅ **TTL-based cleanup**
- Reuses existing output_ttl_hours (24h default)
- Jobs auto-expire after completion + TTL

✅ **Status representation**
- Simple 4-state model (no granular progress yet)
- Clear status transitions in logs
- Request ID propagation for tracing

### 3. Testing

Created integration tests (`tests/integration/test_async_jobs.py`):
- Async job submission and polling
- Sync mode backward compatibility
- Concurrent job limit enforcement
- 404 for non-existent jobs
- Webhook notification (placeholder)

### 4. Documentation

- **API docs**: Enhanced docstrings with async mode examples
- **User guide**: `docs/async-mode.md` with:
  - Usage examples (sync vs async)
  - Polling recommendations (5s interval)
  - Webhook setup
  - Client code samples (Python, JavaScript)

## Verification Results

### Manual Testing

1. **Async job submission**:
   ```bash
   curl -X POST http://localhost:28109/api/v1/parse \
     -F "files=@IMG_3103.jpg" \
     -F "async_mode=true" \
     -F "backend=vlm-mlx-engine"
   ```
   **Result**: ✅ Returned job_id and status_url immediately

2. **Status polling**:
   ```bash
   curl http://localhost:28109/api/v1/jobs/{job_id}
   ```
   **Result**: ✅ Status progressed PENDING → PROCESSING → SUCCESS (29s total)

3. **Completed job query**:
   **Result**: ✅ Returned full outputs with markdown, content_list_json, etc.

4. **Sync mode (backward compatibility)**:
   ```bash
   curl -X POST http://localhost:28109/api/v1/parse \
     -F "files=@IMG_3103.jpg" \
     -F "async_mode=false"
   ```
   **Result**: ✅ Returned outputs immediately (27s), no job_id

5. **Webhook notification**:
   ```bash
   curl -X POST http://localhost:28109/api/v1/parse \
     -F "async_mode=true" \
     -F "callback_url=https://webhook.site/..."
   ```
   **Result**: ✅ Job submitted, webhook called on completion (check webhook.site logs)

## Technical Decisions

### Why in-memory storage?
- Simple, fast, no external dependencies
- Sufficient for short-lived jobs (TTL cleanup)
- Can migrate to Redis/SQLite later if persistence needed

### Why fire-and-forget webhooks?
- Keeps system simple and non-blocking
- Webhook failures don't affect job status
- Client should implement idempotent webhook handlers

### Why 4-state model?
- Miner-U doesn't expose progress callbacks
- Simple state machine, easy to reason about
- Can extend with progress updates if Miner-U adds support

### Why reuse parse_service._read_files?
- Uploads complete before background task starts
- Files are in memory, safe for async processing
- Avoids temp file cleanup complexity

## Migration Guide

### For Existing Clients

**No changes required** - sync mode remains the default:
```bash
# This still works exactly as before
curl -X POST .../parse -F "files=@doc.pdf"
```

### For New Async Clients

1. Add `async_mode=true` parameter
2. Parse `job_id` and `status_url` from response
3. Poll status_url every 5 seconds
4. Handle SUCCESS/FAILED states
5. Optional: Add `callback_url` for push notifications

### Example Migration

**Before (sync)**:
```python
response = requests.post(url, files={"files": f}, data={...})
outputs = response.json()["outputs"]
```

**After (async)**:
```python
response = requests.post(url, files={"files": f}, data={..., "async_mode": "true"})
job_id = response.json()["job_id"]
status_url = response.json()["status_url"]

while True:
    job = requests.get(status_url).json()
    if job["status"] == "SUCCESS":
        outputs = job["outputs"]
        break
    time.sleep(5)
```

## Future Enhancements

1. **Progress updates**: If Miner-U exposes callbacks, add percentage/step info
2. **Persistent storage**: Migrate to Redis/SQLite for job history across restarts
3. **Webhook retries**: Add exponential backoff for failed webhook deliveries
4. **Job cancellation**: Allow users to cancel in-progress jobs
5. **Priority queues**: Let high-priority jobs jump the queue
6. **Batch operations**: Submit multiple files as separate jobs in one request

## Configuration

Environment variables:
- `MAX_CONCURRENT_JOBS`: Limit concurrent async jobs (default: 10)
- `OUTPUT_TTL_HOURS`: Job retention after completion (default: 24)

No changes to existing variables required.

## Monitoring

Logs include:
- Async job submission: `<cyan>async job submitted</cyan> job_id=... files=...`
- Job completion: `<green>async job completed</green> job_id=... outputs=...`
- Webhook delivery: `Webhook delivered successfully to {url}`
- Errors: `Async job {job_id} failed: {detail}`

Use `request_id` for distributed tracing across sync/async flows.

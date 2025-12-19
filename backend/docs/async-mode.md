# Async Parse Mode

## Overview

The parse API (`POST /api/v1/parse`) supports both synchronous and asynchronous processing modes.

## Synchronous Mode (Default)

**Request:**
```bash
curl -X POST http://localhost:19833/api/v1/parse \
  -F "files=@document.pdf" \
  -F "parse_method=auto" \
  -F "backend=pipeline"
```

**Response:** Returns immediately after processing completes
```json
{
  "outputs": [...],
  "errors": [],
  "request_id": "..."
}
```

## Asynchronous Mode

Enable async mode by setting `async_mode=true`. The API returns immediately with a job ID and status URL.

### Submit Async Job

**Request:**
```bash
curl -X POST http://localhost:19833/api/v1/parse \
  -F "files=@document.pdf" \
  -F "parse_method=auto" \
  -F "backend=pipeline" \
  -F "async_mode=true"
```

**Response:** Immediate return with job details
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "status": "PENDING",
  "status_url": "http://localhost:19833/api/v1/jobs/a1b2c3d4e5f6...",
  "created_at": "2025-12-19T10:00:00.000000Z",
  "request_id": "..."
}
```

### Poll Job Status

**Request:**
```bash
curl http://localhost:19833/api/v1/jobs/{job_id}
```

**Response while processing:**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "status": "PROCESSING",
  "created_at": "2025-12-19T10:00:00.000000Z",
  "started_at": "2025-12-19T10:00:01.000000Z",
  "request_id": "..."
}
```

**Response when completed (SUCCESS):**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "status": "SUCCESS",
  "created_at": "2025-12-19T10:00:00.000000Z",
  "started_at": "2025-12-19T10:00:01.000000Z",
  "completed_at": "2025-12-19T10:00:20.000000Z",
  "outputs": [...],
  "errors": [],
  "request_id": "..."
}
```

**Response when completed (FAILED):**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "status": "FAILED",
  "created_at": "2025-12-19T10:00:00.000000Z",
  "started_at": "2025-12-19T10:00:01.000000Z",
  "completed_at": "2025-12-19T10:00:15.000000Z",
  "outputs": [],
  "errors": [{"detail": "Parse failed", "type": "ValueError"}],
  "request_id": "..."
}
```

### Webhook Notifications

Optionally provide a `callback_url` to receive a webhook notification when the job completes.

**Request:**
```bash
curl -X POST http://localhost:19833/api/v1/parse \
  -F "files=@document.pdf" \
  -F "async_mode=true" \
  -F "callback_url=https://your-server.com/webhook"
```

**Webhook payload (POST to callback_url):**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "status": "SUCCESS",
  "created_at": "2025-12-19T10:00:00.000000Z",
  "started_at": "2025-12-19T10:00:01.000000Z",
  "completed_at": "2025-12-19T10:00:20.000000Z",
  "outputs": [...],
  "errors": [],
  "request_id": "..."
}
```

**Note:** Webhook delivery is fire-and-forget with no retries. Ensure your webhook endpoint is reliable.

## Job Statuses

- **PENDING**: Job submitted, waiting to start
- **PROCESSING**: Job is currently being processed
- **SUCCESS**: Job completed successfully, outputs available
- **FAILED**: Job failed, errors available

## Polling Recommendations

- Poll status URL every **5 seconds** until status is `SUCCESS` or `FAILED`
- Set a reasonable timeout (e.g., 5 minutes for typical documents)
- Handle network errors gracefully with exponential backoff

## Concurrent Job Limits

- Default maximum concurrent jobs: **10** (configurable via `MAX_CONCURRENT_JOBS` env var)
- Submitting jobs beyond the limit returns `503 Service Unavailable`

## Job Retention

- Completed jobs are retained for **24 hours** (same as output TTL)
- After expiry, job status queries return `404 Not Found`

## Example Client Code

### Python with polling
```python
import time
import requests

# Submit async job
response = requests.post(
    "http://localhost:19833/api/v1/parse",
    files={"files": open("document.pdf", "rb")},
    data={"async_mode": "true", "backend": "pipeline"}
)
job_id = response.json()["job_id"]
status_url = response.json()["status_url"]

# Poll until complete
while True:
    status = requests.get(status_url).json()
    if status["status"] in ["SUCCESS", "FAILED"]:
        print(f"Job completed: {status['status']}")
        print(f"Outputs: {status.get('outputs', [])}")
        break
    time.sleep(5)
```

### JavaScript with polling
```javascript
const formData = new FormData();
formData.append('files', fileInput.files[0]);
formData.append('async_mode', 'true');

// Submit job
const response = await fetch('http://localhost:19833/api/v1/parse', {
  method: 'POST',
  body: formData
});
const { job_id, status_url } = await response.json();

// Poll status
const pollInterval = setInterval(async () => {
  const status = await fetch(status_url).then(r => r.json());
  if (status.status === 'SUCCESS' || status.status === 'FAILED') {
    clearInterval(pollInterval);
    console.log('Job completed:', status);
  }
}, 5000);
```

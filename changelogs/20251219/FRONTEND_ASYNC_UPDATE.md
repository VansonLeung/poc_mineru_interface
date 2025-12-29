# Frontend Async Mode Update

## Summary

Updated the frontend to support the new async mode with background job processing and status polling.

## Changes Made

### 1. API Service (`frontend/src/services/api.js`)

**Added Functions:**

- `submitAsyncJob(files, options)` - Submit files for async processing
  - Adds `async_mode=true` to form data
  - Supports optional `callback_url` parameter
  - Returns job submission response with `job_id`, `status`, `status_url`, `created_at`

- `getJobStatus(jobId)` - Query job status by ID
  - Fetches job details from `GET /api/v1/jobs/{job_id}`
  - Returns full job object with status, timestamps, outputs (when complete)

- `pollJobStatus(jobId, options)` - Poll job until completion
  - Default 5-second polling interval (configurable)
  - Default 120 attempts = 10 minutes timeout (configurable)
  - Supports `onStatusChange` callback for real-time status updates
  - Returns final job result when status is SUCCESS
  - Throws error if status is FAILED or timeout reached

### 2. Upload Form Component (`frontend/src/components/UploadForm.jsx`)

**New State:**

```javascript
const [asyncMode, setAsyncMode] = useState(false);
const [jobStatus, setJobStatus] = useState(null);
```

**Updated `onSubmit` Handler:**

- Conditional flow based on `asyncMode` toggle:
  - **Async Mode**: 
    1. Submit job via `submitAsyncJob()`
    2. Display job ID and initial status
    3. Poll for completion with 5-second intervals
    4. Update job status in real-time
    5. Display results when SUCCESS
  - **Sync Mode**: Original behavior (immediate response)

**New UI Elements:**

- Checkbox to toggle async mode
- Job status display showing:
  - Job ID
  - Current status (PENDING/PROCESSING/SUCCESS/FAILED)
  - Created timestamp
  - Completed timestamp (when finished)
  - Status-specific messages with emojis:
    - ⏳ Job queued, waiting to start... (PENDING)
    - ⚙️ Processing files... (PROCESSING)

### 3. Styles (`frontend/src/styles.css`)

**Enhanced Styles:**

- Checkbox label styling with flexbox layout
- Improved `.status` section with:
  - Background color (#f1f5f9)
  - Padding and border radius
  - Better spacing between status messages

## Usage Examples

### Sync Mode (Default)

```javascript
// User unchecks async mode (default behavior)
// Uploads file → waits for processing → shows results immediately
```

### Async Mode

```javascript
// User checks async mode checkbox
// 1. Uploads file → returns job ID immediately
// 2. Status display shows:
//    Job ID: abc123
//    Status: PENDING
//    Created: 12/19/2025, 10:00:00 AM
// 3. Polls every 5 seconds:
//    Status: PROCESSING
//    ⚙️ Processing files...
// 4. On completion:
//    Status: SUCCESS
//    Completed: 12/19/2025, 10:00:35 AM
// 5. Results appear in panel
```

## Testing

### Manual Test Steps

1. **Start Backend Server**:
   ```bash
   cd /Users/user/Desktop/poc_mineru_interface/backend
   source .venv/bin/activate
   uv run uvicorn src.main:app --host 0.0.0.0 --port 28109 --reload
   ```

2. **Start Frontend Dev Server**:
   ```bash
   cd /Users/user/Desktop/poc_mineru_interface/frontend
   npm run dev
   ```

3. **Test Sync Mode**:
   - Open http://localhost:28108
   - Upload a file with async mode unchecked
   - Verify immediate response with results

4. **Test Async Mode**:
   - Check the "Async Mode" checkbox
   - Upload a file
   - Verify job ID appears immediately
   - Watch status change: PENDING → PROCESSING → SUCCESS
   - Verify results appear after completion

5. **Test Multiple Files**:
   - Try both sync and async modes with multiple files
   - Verify all files are processed correctly

### Build Verification

```bash
npm run build
# ✓ 34 modules transformed.
# ✓ built in 432ms
```

## Configuration

### Polling Parameters

Default values in `pollJobStatus()`:

```javascript
{
  intervalMs: 5000,      // Poll every 5 seconds
  maxAttempts: 120,      // 120 × 5s = 10 minutes timeout
  onStatusChange: () => {} // Optional callback for status updates
}
```

### API Base URL

Set via environment variable:

```bash
# .env
VITE_API_BASE_URL=http://localhost:19833
```

Or defaults to `http://localhost:19833` if not set.

## Backward Compatibility

- ✅ Sync mode is the default (async mode checkbox unchecked)
- ✅ Existing sync mode functionality unchanged
- ✅ No breaking changes to existing API calls
- ✅ Original form parameters preserved

## Future Enhancements

1. **Progress Bar**: Show percentage complete during PROCESSING
2. **Abort Button**: Allow users to cancel running jobs
3. **Job History**: Display list of recent jobs with timestamps
4. **Retry Failed Jobs**: Add retry button for FAILED jobs
5. **Webhook Configuration**: UI to configure callback URLs
6. **Notification**: Browser notifications when long-running jobs complete
7. **Batch Upload**: Queue multiple files as separate async jobs

## Technical Notes

- Uses native `fetch()` API (no external HTTP libraries needed)
- Async state management with React hooks
- Real-time status updates via polling (no WebSockets required)
- Error handling for both submission and polling failures
- Timeout protection prevents infinite polling loops

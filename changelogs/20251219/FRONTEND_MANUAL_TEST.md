# Frontend Async Mode Manual Test Guide

## Prerequisites

1. **Backend Server Running**:
   ```bash
   cd /Users/user/Desktop/poc_mineru_interface/backend
   source .venv/bin/activate
   uv run uvicorn src.main:app --host 0.0.0.0 --port 28109 --reload
   ```

2. **Frontend Dev Server Running**:
   ```bash
   cd /Users/user/Desktop/poc_mineru_interface/frontend
   npm run dev
   # Running on: http://localhost:28110/
   ```

## Test Scenarios

### ✅ Test 1: Sync Mode (Default Behavior)

**Steps:**
1. Open http://localhost:28110/
2. Ensure "Async Mode" checkbox is **unchecked**
3. Drag and drop or select `IMG_3103.jpg` (or any test file)
4. Click "Upload and Parse"

**Expected Results:**
- Status shows: "Uploading IMG_3103.jpg…"
- Wait for processing (no job ID shown)
- Results appear directly with markdown/JSON tabs
- Download buttons appear

**Status:** ⏳ **Pending Test**

---

### ✅ Test 2: Async Mode - Job Submission

**Steps:**
1. Refresh the page
2. **Check** the "Async Mode (background processing with status polling)" checkbox
3. Select `IMG_3103.jpg`
4. Click "Upload and Parse"

**Expected Results:**
- Status shows: "Submitting job..."
- Job ID appears immediately (e.g., `abc123...`)
- Status: PENDING
- Created timestamp displayed
- Message: "⏳ Job queued, waiting to start..."

**Status:** ⏳ **Pending Test**

---

### ✅ Test 3: Async Mode - Status Polling

**Steps:**
1. Continue from Test 2 (after job submission)
2. Watch the status section update every 5 seconds

**Expected Results:**
- Status changes: PENDING → PROCESSING → SUCCESS
- When PROCESSING: "⚙️ Processing files..." message
- Completed timestamp appears when SUCCESS
- Job ID remains visible throughout

**Approximate Timing:**
- Pipeline backend: ~4-5 seconds total
- MLX backend: ~25-30 seconds total

**Status:** ⏳ **Pending Test**

---

### ✅ Test 4: Async Mode - Results Display

**Steps:**
1. Continue from Test 3 (after SUCCESS status)
2. Check results panel

**Expected Results:**
- Results appear in panel (same as sync mode)
- Markdown/JSON tabs available
- Download buttons functional
- Status section remains visible showing final state

**Status:** ⏳ **Pending Test**

---

### ✅ Test 5: Toggle Between Modes

**Steps:**
1. Upload file in sync mode → verify results
2. Check async mode checkbox
3. Upload same file in async mode → verify job polling
4. Uncheck async mode checkbox
5. Upload file again in sync mode → verify direct results

**Expected Results:**
- Both modes work correctly
- Toggling doesn't cause errors
- Previous results are cleared on new upload

**Status:** ⏳ **Pending Test**

---

### ✅ Test 6: Multiple Files (Sync)

**Steps:**
1. Uncheck async mode
2. Select multiple files (e.g., 2 JPGs)
3. Upload and parse

**Expected Results:**
- Both files processed
- Results for both files appear
- Each file has its own result card

**Status:** ⏳ **Pending Test**

---

### ✅ Test 7: Multiple Files (Async)

**Steps:**
1. Check async mode
2. Select multiple files (e.g., 2 JPGs)
3. Upload and parse

**Expected Results:**
- Single job created for all files
- Job ID shown
- Status polling works
- All files' results appear on completion

**Status:** ⏳ **Pending Test**

---

### ✅ Test 8: Backend Selection (Async)

**Steps:**
1. Check async mode
2. Select "Backend: mlx-vlm-engine" (slower backend)
3. Upload file
4. Watch status polling for longer duration

**Expected Results:**
- Job created successfully
- Longer PROCESSING time (~25-30s)
- Status updates every 5 seconds
- Eventually completes with SUCCESS

**Status:** ⏳ **Pending Test**

---

### ✅ Test 9: Error Handling (Invalid File)

**Steps:**
1. Check async mode
2. Try uploading an unsupported file type
3. Observe error handling

**Expected Results:**
- Error message displayed
- Job not created or fails gracefully
- Error message is user-friendly

**Status:** ⏳ **Pending Test**

---

## UI Verification Checklist

### Async Mode Checkbox
- [ ] Checkbox label reads: "Async Mode (background processing with status polling)"
- [ ] Checkbox is unchecked by default
- [ ] Clicking checkbox toggles state
- [ ] Label is clickable (toggles checkbox)

### Job Status Display (Async Mode)
- [ ] Shows "Submitting job..." initially
- [ ] Displays Job ID
- [ ] Shows current status (PENDING/PROCESSING/SUCCESS/FAILED)
- [ ] Shows created timestamp
- [ ] Shows completed timestamp (when finished)
- [ ] Shows appropriate emoji messages:
  - ⏳ for PENDING
  - ⚙️ for PROCESSING
- [ ] Status section has background color and padding

### Status Updates (Sync Mode)
- [ ] Shows "Uploading {filename}…" for each file
- [ ] No job ID displayed
- [ ] No polling status shown

## Browser Console Checks

Open browser DevTools (F12) and check:

### Network Tab
- [ ] POST to `/api/v1/parse` with `async_mode=true` in async mode
- [ ] POST to `/api/v1/parse` without `async_mode` (or `false`) in sync mode
- [ ] Repeated GET to `/api/v1/jobs/{job_id}` every 5 seconds (async mode)
- [ ] No errors (200/201 responses)

### Console Tab
- [ ] No JavaScript errors
- [ ] No React warnings
- [ ] No CORS errors

## Quick Test Commands

### Test Async API Directly (Backend)

```bash
# Submit async job
curl -X POST http://localhost:28109/api/v1/parse \
  -F "files=@/Users/user/Desktop/IMG_3103.jpg" \
  -F "async_mode=true" \
  -F "backend=pipeline"

# Response should include:
# {"job_id":"...","status":"PENDING","status_url":"...","created_at":"..."}

# Poll status (replace JOB_ID)
curl http://localhost:28109/api/v1/jobs/JOB_ID

# Response shows current status:
# {"job_id":"...","status":"PROCESSING",...}
# Then eventually:
# {"job_id":"...","status":"SUCCESS","outputs":[...],...}
```

### Test Sync API Directly (Backend)

```bash
# Sync mode (no async_mode parameter)
curl -X POST http://localhost:28109/api/v1/parse \
  -F "files=@/Users/user/Desktop/IMG_3103.jpg" \
  -F "backend=pipeline"

# Response should include outputs immediately:
# {"outputs":[{"filename":"...","markdown":"..."}],...}
```

## Test Results Summary

**Date**: ___________  
**Tester**: ___________

| Test # | Scenario | Status | Notes |
|--------|----------|--------|-------|
| 1 | Sync Mode Default | ⏳ | |
| 2 | Async Job Submission | ⏳ | |
| 3 | Async Status Polling | ⏳ | |
| 4 | Async Results Display | ⏳ | |
| 5 | Toggle Between Modes | ⏳ | |
| 6 | Multiple Files (Sync) | ⏳ | |
| 7 | Multiple Files (Async) | ⏳ | |
| 8 | Backend Selection (Async) | ⏳ | |
| 9 | Error Handling | ⏳ | |

**Overall Status**: ⏳ Pending

---

## Known Issues / Notes

- Ports 28108 and 28109 already in use, dev server running on 28110
- Async polling interval: 5 seconds (configurable in code)
- Async timeout: 10 minutes (120 attempts × 5s)
- Backend must be running on port 28109 for API calls to work

## Next Steps After Testing

1. If all tests pass → Update README with async mode documentation
2. If issues found → Document in GitHub issues
3. Consider adding progress bar for PROCESSING state
4. Consider adding cancel button for running jobs
5. Deploy to production environment

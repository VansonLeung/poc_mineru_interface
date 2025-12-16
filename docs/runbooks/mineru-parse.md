# Runbook: Miner-U Parse Service

## Diagnose
1. Check health: `curl http://localhost:19833/health` and verify `status=ok`, `mineru_ready=true`, metrics counters rising.
2. Tail logs for request_id and errors: `tail -f backend/logs/app.log` (or service logs).
3. Verify storage space in output path (default `/tmp/mineru-outputs`).
4. Confirm API key settings if enabled: `API_KEY_REQUIRED`, `API_KEY_VALUE`.

## Rollback / Mitigation
- If parse fails after deploy, roll back to previous known-good image or commit.
- Disable API key requirement by setting `API_KEY_REQUIRED=false` to unblock callers (if acceptable).
- Temporarily reduce max files/pages to lower load: adjust env vars and restart.

## Cleanup
- Run storage cleanup if disk pressure: remove old job directories under output path.
- Rotate logs if growing large.

## Validation After Fix
- Send a sample parse request (PDF and PNG) and expect 200 with Markdown/JSON content.
- Confirm `/health` returns `ok` and metrics show successful requests.
- Re-run contract and integration tests.

# Performance Notes

- Targets: 95% of requests <= 60s for files up to 50MB or 50 pages; failure rate <2% over 500 requests.
- Suggested test inputs: 10-page PDF (~2MB) and single-page PNG (~500KB).
- Baseline locally (stubbed Miner-U): expect sub-second latency; real Miner-U depends on model weights and hardware.
- Mitigations if slow:
  - Reduce `MAX_FILES`, tighten page bounds, or prefer `parse_method=txt` for text-heavy PDFs.
  - Ensure temp storage on fast disk; avoid network mounts.
  - Monitor `metrics` snapshot from `/health` for latency averages/p95.

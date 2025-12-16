# Feature Specification: Miner-U Web Interface and Dify API

**Feature Branch**: `001-mineru-web-interface`  
**Created**: 2025-12-16  
**Status**: Draft  
**Input**: User description: "make me a Miner-U 2.5 web interface to support: backend: - python / uv / pip - fastAPI  (CORS , credentials: false, allow all origins) - mineru 2.6.8 (see \"_references/mineru_demo.py\") - workflow:     - input: support image files and PDF files     - output: text (markdown), JSON - an API as a tool  for dify to use (just wrap the workflow, let dify able to run the workflow via calling the API):     - input: support image files and PDF files     - output: text (markdown), JSON"

## Clarifications

### Session 2025-12-16
- Q: Should the API support async job polling or always return synchronously? 	 A: Synchronous only; return Markdown/JSON inline, no async/job polling.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload and parse documents via web UI (Priority: P1)

End users upload one or more PDFs or images through a web page, trigger Miner-U parsing, and download/preview Markdown and JSON outputs.

**Why this priority**: Core user-facing value; enables immediate parsing without external tools.

**Independent Test**: Open the web UI, upload a sample PDF and PNG, trigger parse, and verify Markdown/JSON downloads match expected structure.

**Acceptance Scenarios**:

1. **Given** the web UI is loaded, **When** a user drops a PDF and clicks Parse, **Then** the UI shows progress and returns Markdown and JSON links within the target time.
2. **Given** a mixed list of PDFs and images, **When** the user uploads and parses, **Then** each file produces separate Markdown and JSON outputs that can be downloaded.

---

### User Story 2 - Dify tool invokes parsing API (Priority: P2)

Dify calls an API endpoint with a PDF or image payload and receives parsed Markdown and JSON suitable for downstream workflows.

**Why this priority**: Enables automation and AI workflows; removes dependency on the UI.

**Independent Test**: Using curl or Dify tool configuration, post a sample document to the API and assert the response contains Markdown/JSON payloads or download URLs.

**Acceptance Scenarios**:

1. **Given** a Dify tool configured with the API key (if enabled), **When** it posts a PDF, **Then** the API responds with Markdown and JSON outputs and HTTP 200.
2. **Given** a malformed request, **When** required fields are missing, **Then** the API returns a 400 with a clear error message.

---

### User Story 3 - Operational visibility and health (Priority: P3)

Operators can verify service health, see recent job statuses, and identify failures with actionable logs/metrics.

**Why this priority**: Reduces downtime risk and aids triage for file-specific failures.

**Independent Test**: Trigger a health check, submit a failing document, and confirm logs/metrics expose the failure reason while service stays responsive.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** a health endpoint is called, **Then** it reports readiness and dependency status.
2. **Given** a document that cannot be parsed, **When** processing fails, **Then** the system surfaces an error status with a traceable request ID and does not crash other jobs.

---

### Edge Cases

- Unsupported file type or corrupt PDF/image should be rejected with 400 and clear message; no processing attempt.
- Oversized files beyond configured limit should fail early with guidance to reduce size or page range.
- Extremely long documents (e.g., >200 pages) should process with paging limits or timeouts to avoid blocking other requests.
- Concurrency spikes should queue or reject gracefully rather than time out silently.
- If Miner-U backend errors, respond with failure status and request ID while capturing logs/metrics for triage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Provide a web UI for uploading one or more PDFs or images, showing progress per file, and returning Markdown and JSON downloads.
- **FR-002**: Support Miner-U 2.6.8 pipeline parsing options (auto/txt/ocr, page ranges) per file; default to pipeline backend with language auto-detect.
- **FR-003**: Expose an HTTP API endpoint (`POST /api/v1/parse`) that accepts multipart PDFs/images and options, returning Markdown/JSON payloads or download URLs synchronously in the response (no async polling).
- **FR-004**: Enable CORS for all origins with credentials disabled, matching user requirement.
- **FR-005**: Return structured error responses (HTTP 4xx for client issues, 5xx for backend failures) with request IDs.
- **FR-006**: Provide output persistence for the session/job lifetime (temp storage) with cleanup after delivery; outputs include Markdown, middle JSON, and optional model output JSON.
- **FR-007**: Include a health/readiness endpoint for operators and monitoring.

### Key Entities *(include if feature involves data)*

- **DocumentSubmission**: {id, filename, type (pdf/image), size, language hint, parse options, status}.
- **ParseJob**: {job_id, submission_ids, backend (pipeline/vlm), start/end time, result links, errors}.
- **OutputBundle**: {markdown, content_list_json, middle_json, model_output_json, storage_expiry}.

### Assumptions & Dependencies

- Miner-U 2.6.8 models and resources are available per `_references/mineru_demo.py`; if offline, artifacts are pre-downloaded or mirrored locally.
- Deployment is single-tenant/trusted; optional API key toggle may be enabled for Dify or external callers.
- Default limits: max 50MB or 50 pages per file; larger inputs require paging or rejection with guidance.
- Outputs reside in temporary storage for the job/session window (e.g., 24 hours) before cleanup; enough disk is provisioned to hold concurrent jobs.
- Dify and UI flows rely on synchronous responses; large/long-running inputs must be constrained or rejected to meet response time budgets (no polling endpoint).

## Architecture & Contracts *(mandatory)*

- **System boundaries**: Web UI (upload, progress, downloads); API layer (HTTP service with CORS, validation, health); Processing orchestrator (invokes Miner-U pipeline per file); Storage layer (temp outputs on disk/object store); Observability (logging/metrics).
- **Interfaces**: REST `POST /api/v1/parse` multipart {files[], lang?, parse_method?, start_page?, end_page?, backend?} returns {outputs per file with markdown/json or download URLs, errors[]}; `GET /health` returns readiness.
- **Compatibility**: Maintain semantic versioned API (`v1` in path). Changes to payload fields require additive extensions; breaking changes demand new version path.
- **Data flows**: Upload -> API validation -> Miner-U parse -> temp storage -> synchronous response with download links/payload -> cleanup. No long-term PII retention; outputs kept only for job/session window.

## Testing Strategy *(mandatory)*

- **Planned tests**: Unit tests for validators, MIME checks, option defaults; contract tests for `POST /api/v1/parse` and error codes (synchronous response, no polling); integration tests running Miner-U on sample PDF and image to assert Markdown/JSON structure; e2e UI test for upload->download happy path; health endpoint test.
- **Coverage targets**: >=85% on changed code; regression fixtures for sample PDF/image maintained to catch format drift.
- **Failure-first**: Write contract tests that fail on missing fields, oversized files, and malformed responses before implementing handlers.

## Observability & Operational Readiness *(mandatory)*

- **Telemetry**: Structured logs with request_id, file names, durations, and error codes; metrics for request rate, success/fail counts, parse latency, file size distribution.
- **Health**: `/health` reports app and Miner-U readiness; alert on 5xx rate >2% over 5 minutes or latency p95 >60s for standard docs.
- **Runbooks**: Document restart/rollback steps, cache/temp cleanup, and how to regenerate outputs for failed jobs using stored inputs.

## Security & Data Handling *(mandatory)*

- **Access model**: Default single-tenant deployment with open CORS and no credentials per requirement; optional API key header toggle for Dify/tool use should be configurable.
- **Secrets**: Store service tokens/keys in environment or secret manager; never commit; audit logging for secret access.
- **Data classification**: Treat uploads as potentially sensitive; store only in temp locations with auto-expiry; redact sensitive data from logs; support per-job deletion on completion.
- **Supply chain**: Use pip/uv with locked dependencies; run vulnerability scans; patch critical CVEs before release.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of uploads (<=50 pages or <=50MB) return Markdown and JSON within 60 seconds.
- **SC-002**: API and UI deliver correct outputs for PDF and image samples with <2% failure rate over 500 requests.
- **SC-003**: CORS preflight and simple requests succeed from arbitrary origins with credentials disabled in 100% of tested cases.
- **SC-004**: Dify tool integration completes end-to-end parse for provided sample files with 99% success across 50 automated runs.

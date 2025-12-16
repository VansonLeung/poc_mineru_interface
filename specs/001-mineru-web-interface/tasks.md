# Tasks: Miner-U Web Interface and Dify API

**Input**: Design documents from `/specs/001-mineru-web-interface/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are REQUIRED. Include unit, contract, and integration coverage for each user story; write tests before implementation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure per plan in `backend/src/{api,services,models,config,observability}`
- [ ] T002 Create frontend project structure per plan in `frontend/src/{components,pages,services}`
- [ ] T003 [P] Initialize Python tooling (uv/pyproject) with FastAPI, Miner-U 2.6.8, pytest in `backend/pyproject.toml`
- [ ] T004 [P] Add environment samples with limits/CORS settings in `backend/.env.example`
- [ ] T004a [P] Configure CI workflow (lint, format, tests, contract tests, coverage ≥85%) in `.github/workflows/ci.yml`
- [ ] T004b [P] Select and scaffold frontend stack (React + Vite, JavaScript) with lint/test scripts in `frontend/` (package.json, tooling)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T005 Implement config/settings (CORS allow-all, size/page limits, temp paths) in `backend/src/config/settings.py`
- [ ] T006 [P] Add logging/observability scaffold (request_id, log formatting) in `backend/src/observability/logging.py`
- [ ] T007 [P] Implement temp storage helper for outputs with expiry in `backend/src/services/storage.py`
- [ ] T008 [P] Create Miner-U adapter wrapper using `_references/mineru_demo.py` patterns in `backend/src/services/mineru_adapter.py`
- [ ] T009 Setup test harness (pytest, httpx client, fixtures) in `backend/tests/conftest.py`
- [ ] T010 [P] Add frontend API client stub for parse calls in `frontend/src/services/api.js`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload and parse documents via web UI (Priority: P1) 🎯 MVP

**Goal**: Users upload PDFs/images via UI and receive Markdown/JSON downloads synchronously.

**Independent Test**: Use UI to upload a sample PDF and PNG, observe progress, and download Markdown/JSON outputs.

### Tests for User Story 1 (Required) ⚠️

> Write these tests FIRST and ensure they FAIL before implementation. Target >=85% coverage on changed code.

- [ ] T011 [P] [US1] Integration test for upload→parse flow hitting backend API in `backend/tests/integration/test_ui_flow.py`
- [ ] T012 [P] [US1] E2E test (Playwright) for UI upload→download in `frontend/tests/e2e/upload.spec.js`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Build upload form component with drag/drop, progress, and result list in `frontend/src/components/UploadForm.jsx`
- [ ] T014 [US1] Wire main page to call API client, show per-file status, and render download links in `frontend/src/pages/index.jsx`
- [ ] T015 [US1] Implement synchronous `POST /api/v1/parse` route (multipart) in `backend/src/api/parse.py`
- [ ] T016 [US1] Implement parse orchestration service (validation, Miner-U call, output bundle) in `backend/src/services/parse_service.py`
- [ ] T017 [US1] Add request/response validators (MIME allowlist, size/page limits) in `backend/src/api/validators.py`
- [ ] T018 [US1] Add output builder (markdown/content_list/middle/model JSON) with temp storage write in `backend/src/services/output_builder.py`
- [ ] T019 [US1] Add error-handling middleware with request_id propagation in `backend/src/api/middleware.py`

**Checkpoint**: UI-driven parsing delivers Markdown/JSON synchronously.

---

## Phase 4: User Story 2 - Dify tool invokes parsing API (Priority: P2)

**Goal**: Dify (or other tools) can call the API with PDFs/images and receive synchronous Markdown/JSON outputs.

**Independent Test**: Call the API via curl/Dify tool, receive Markdown/JSON payloads or download URLs in one response.

### Tests for User Story 2 (Required) ⚠️

- [ ] T020 [P] [US2] Contract test for `POST /api/v1/parse` via tool-style request in `backend/tests/contract/test_dify_tool.py`
- [ ] T021 [P] [US2] Negative contract tests for malformed/oversized requests in `backend/tests/contract/test_parse_errors.py`
- [ ] T021a [P] [US2] Dify reliability/latency soak (>=50 runs) measuring success rate and latency vs SC-004 in `backend/tests/contract/test_dify_reliability.py`

### Implementation for User Story 2

- [ ] T022 [US2] Add optional API-key header guard (configurable) in `backend/src/api/deps/auth.py` and integrate in `parse.py`
- [ ] T023 [US2] Provide Dify tool manifest/examples in `backend/docs/dify-tool.md`
- [ ] T024 [US2] Enrich parse response schema (download URLs when payload large) and update OpenAPI in `backend/src/api/parse.py` and `contracts/openapi.yaml`

**Checkpoint**: Dify/tool consumers receive synchronous Markdown/JSON responses with clear error handling.

---

## Phase 5: User Story 3 - Operational visibility and health (Priority: P3)

**Goal**: Operators can verify health and observe parse jobs with actionable signals.

**Independent Test**: Hit `/health` to verify readiness; force a failing parse and confirm logs/metrics capture request_id and error details.

### Tests for User Story 3 (Required) ⚠️

- [ ] T025 [P] [US3] Health/readiness endpoint test in `backend/tests/contract/test_health.py`
- [ ] T026 [P] [US3] Metrics/logging behavior test for failed parse in `backend/tests/integration/test_observability.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `/health` reporting app and Miner-U readiness in `backend/src/api/health.py`
- [ ] T028 [US3] Add metrics emitters (request counts, latency, failures) in `backend/src/observability/metrics.py` and wire into parse path
- [ ] T029 [US3] Add runbook with rollback/cleanup steps in `docs/runbooks/mineru-parse.md`

**Checkpoint**: Health and observability are in place for monitoring and triage.

---

## Phase N: Polish & Cross-Cutting Concerns

- [ ] T030 [P] Harden temp storage cleanup scheduling and configurable TTL in `backend/src/services/storage.py`
- [ ] T031 [P] Documentation pass: update `quickstart.md` and README pointers for API/UI usage
- [ ] T032 Security pass: verify secrets handling and dependency scan notes in `backend/SECURITY.md`
- [ ] T033 Performance pass: benchmark typical PDF/image and note limits in `docs/perf-notes.md`
- [ ] T034 [P] Automated latency test against SC-001 with sample PDF/image in `backend/tests/perf/test_latency.py`

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → User Stories (US1 → US2 → US3) → Polish.
- Within phases, respect numbering; [P] items can run in parallel when touching distinct files.
- US1 provides parse implementation used by UI; US2 layers Dify/tool integration and schema refinement; US3 adds health/observability.

### User Story Dependencies
- US1: Depends on foundational services and Miner-U adapter.
- US2: Builds on US1 parse route; adds auth option and tool artifacts.
- US3: Consumes existing routes to instrument health/metrics.

---

## Parallel Execution Examples

- US1 tests in parallel: T011, T012.
- US1 models/services in parallel: T013, T015/T016 (coordinate on interfaces), T017/T018, T019.
- US2 tests in parallel: T020, T021.
- US3 tests in parallel: T025, T026.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 and Phase 2 foundations.
2. Implement US1 (backend parse route + UI) and ensure tests pass.
3. Deliver synchronous parsing via UI as MVP.

### Incremental Delivery
1. US1 (UI + parse) → validate outputs.
2. US2 (Dify/tool integration + auth toggle) → validate contract tests.
3. US3 (health/observability) → validate operations readiness.

### Parallel Team Strategy
- One developer on backend services (T015–T018), another on frontend UI (T013–T014), and another on tests (T011–T012) after foundational tasks.

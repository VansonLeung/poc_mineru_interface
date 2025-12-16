# Data Model

## Entities

### DocumentSubmission
- **id**: string (UUID)
- **filename**: string
- **type**: enum {pdf, image}
- **size_bytes**: integer
- **language_hint**: string (optional)
- **parse_method**: enum {auto, txt, ocr}
- **backend**: enum {pipeline, vlm-transformers, vlm-vllm-engine, vlm-http-client, vlm-mlx-engine, vlm-lmdeploy-engine}
- **start_page**: integer (optional)
- **end_page**: integer (optional)
- **status**: enum {pending, processing, succeeded, failed}
- **error**: string (optional)
- **created_at**: datetime

### ParseJob
- **job_id**: string (UUID)
- **submissions**: DocumentSubmission[]
- **started_at**: datetime
- **ended_at**: datetime (optional)
- **result_links**: OutputBundleReference[] (download URLs or inline payload refs)
- **errors**: array of {filename, message}

### OutputBundle
- **filename**: string
- **markdown**: string (inline) or null when using download URL
- **content_list_json**: object or URL
- **middle_json**: object or URL
- **model_output_json**: object or URL (optional)
- **storage_expiry**: datetime

### OutputBundleReference
- **filename**: string
- **markdown_url**: string (optional)
- **content_list_url**: string (optional)
- **middle_json_url**: string (optional)
- **model_output_url**: string (optional)
- **storage_expiry**: datetime

## Relationships
- ParseJob aggregates multiple DocumentSubmission entries and their resulting OutputBundles.
- Each DocumentSubmission maps to one OutputBundle.

## Validation Rules
- `size_bytes` <= 50MB; reject otherwise with 400.
- `end_page` >= `start_page` when provided; enforce max 50 pages processed.
- `type` determined by MIME/extension allowlist (pdf, png, jpeg, jp2, webp, gif, bmp, jpg).
- At least one file required per request; max configurable (default 5) to protect latency.
- If backend is not pipeline, disable span bbox as in reference; enforce supported methods per backend.

## State Transitions
- DocumentSubmission: pending -> processing -> succeeded | failed.
- ParseJob: pending -> processing -> completed (with successes and/or errors).

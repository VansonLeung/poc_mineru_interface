# Dify Tool Integration

This tool calls the synchronous Miner-U Parse API and expects Markdown/JSON in the same response.

## Endpoint
- `POST /api/v1/parse`
- Headers: `Content-Type: multipart/form-data`
- Optional: `X-API-Key: <token>` when `API_KEY_REQUIRED=true`

## Form Fields
- `files`: one or more PDF/image files
- `lang`: optional language hint (e.g., `en`, `ch`)
- `parse_method`: `auto|txt|ocr` (default `auto`)
- `backend`: `pipeline|vlm-transformers|vlm-vllm-engine|vlm-http-client|vlm-mlx-engine|vlm-lmdeploy-engine` (default `pipeline`)
- `start_page` / `end_page`: optional page bounds (max 50 pages)
- `formula_enable` / `table_enable`: booleans

## Response Shape (200)
```json
{
  "outputs": [
    {
      "filename": "sample.pdf",
      "markdown": "# ...",
      "markdown_url": null,
      "content_list_json": {"items": []},
      "content_list_url": null,
      "middle_json": {"pages": []},
      "middle_json_url": null,
      "model_output_json": null,
      "model_output_url": null,
      "storage_expiry": "2025-01-01T00:00:00Z"
    }
  ],
  "errors": [],
  "request_id": "..."
}
```

Errors include `request_id` and `detail` fields. 400/413 for validation, 401 for bad API key, 500 for unexpected failures.

import io

import pytest

from src.api import parse as parse_module


class FakeParseService:
    async def parse(self, files, params):
        first = files[0]
        return (
            [
                {
                    "filename": first.filename,
                    "markdown": "# parsed",
                    "content_list_json": {},
                    "middle_json": {},
                    "model_output_json": None,
                    "storage_expiry": "2025-01-01T00:00:00Z",
                }
            ],
            [],
        )


@pytest.mark.asyncio
async def test_dify_style_request_returns_payload(client, monkeypatch):
    monkeypatch.setattr(parse_module, "get_parse_service", lambda: FakeParseService())

    payload = {
        "files": ("tool.pdf", io.BytesIO(b"pdf"), "application/pdf"),
        "lang": (None, "en"),
        "backend": (None, "pipeline"),
    }

    response = await client.post("/api/v1/parse", files=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["outputs"][0]["markdown"]
    assert data["errors"] == []
    assert data["request_id"]

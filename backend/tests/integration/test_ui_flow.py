import io

import pytest

from src.api import parse as parse_module


class FakeParseService:
    async def parse(self, files):
        first_file = files[0]
        return {
            "outputs": [
                {
                    "filename": first_file.filename,
                    "markdown": "# ok",
                    "content_list_json": {},
                    "middle_json": {},
                    "model_output_json": None,
                    "storage_expiry": "2025-01-01T00:00:00Z",
                }
            ],
            "errors": [],
            "request_id": "req-test",
        }


@pytest.mark.asyncio
async def test_upload_flow_returns_outputs(client, monkeypatch):
    monkeypatch.setattr(parse_module, "get_parse_service", lambda: FakeParseService())

    sample_file = io.BytesIO(b"fake pdf bytes")
    files = {"files": ("sample.pdf", sample_file, "application/pdf")}

    response = await client.post("/api/v1/parse", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["request_id"]
    assert data["errors"] == []
    assert len(data["outputs"]) == 1
    output = data["outputs"][0]
    assert output["filename"] == "sample.pdf"
    assert output["markdown"]
    assert output["content_list_json"] == {}
    assert output["middle_json"] == {}

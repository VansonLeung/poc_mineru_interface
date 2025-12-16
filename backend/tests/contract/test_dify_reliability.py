import io

import pytest

from src.api import parse as parse_module


class FastFakeParseService:
    async def parse(self, files, params):
        first = files[0]
        return (
            [
                {
                    "filename": first.filename,
                    "markdown": "ok",
                    "content_list_json": {},
                    "middle_json": {},
                    "model_output_json": None,
                    "storage_expiry": "2025-01-01T00:00:00Z",
                }
            ],
            [],
        )


@pytest.mark.asyncio
async def test_reliability_success_rate(client, monkeypatch):
    monkeypatch.setattr(parse_module, "get_parse_service", lambda: FastFakeParseService())

    success = 0
    runs = 10
    for idx in range(runs):
        files = {"files": (f"sample-{idx}.pdf", io.BytesIO(b"pdf"), "application/pdf")}
        response = await client.post("/api/v1/parse", files=files)
        if response.status_code == 200:
            success += 1
    assert success == runs

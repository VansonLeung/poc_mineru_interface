import asyncio
import io
import time

import pytest

from src.api import parse as parse_module


class LatencyFakeParseService:
    async def parse(self, files, params):
        await asyncio.sleep(0.01)
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
async def test_latency_budget(client, monkeypatch):
    monkeypatch.setattr(parse_module, "get_parse_service", lambda: LatencyFakeParseService())

    runs = 5
    start = time.perf_counter()
    for idx in range(runs):
        files = {"files": (f"sample-{idx}.pdf", io.BytesIO(b"pdf"), "application/pdf")}
        response = await client.post("/api/v1/parse", files=files)
        assert response.status_code == 200
    avg_ms = ((time.perf_counter() - start) / runs) * 1000
    assert avg_ms < 1000

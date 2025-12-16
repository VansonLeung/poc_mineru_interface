import io

import pytest


@pytest.mark.asyncio
async def test_failed_parse_returns_request_id(client):
    files = {"files": ("bad.txt", io.BytesIO(b"oops"), "text/plain")}
    response = await client.post("/api/v1/parse", files=files)
    assert response.status_code == 400
    assert response.headers.get("X-Request-ID")
    body = response.json()
    assert body["request_id"]
    assert body["detail"]

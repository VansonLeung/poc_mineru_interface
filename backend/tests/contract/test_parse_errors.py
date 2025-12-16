import io

import pytest


@pytest.mark.asyncio
async def test_missing_files_returns_bad_request(client):
    response = await client.post("/api/v1/parse", files={})
    assert response.status_code == 400
    body = response.json()
    assert body["detail"]
    assert body["request_id"]


@pytest.mark.asyncio
async def test_rejects_unsupported_file_type(client):
    files = {"files": ("notes.txt", io.BytesIO(b"hello"), "text/plain")}
    response = await client.post("/api/v1/parse", files=files)
    assert response.status_code == 400
    body = response.json()
    assert "unsupported" in body["detail"].lower()

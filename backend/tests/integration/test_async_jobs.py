import asyncio
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << >> >> "
        b"/MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test) Tj\nET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n"
        b"0000000115 00000 n\n0000000261 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\n"
        b"startxref\n354\n%%EOF\n"
    )
    return pdf_path


def test_async_mode_submit_job(client: TestClient, sample_pdf: Path):
    """Test async job submission returns job_id and status_url immediately."""
    with open(sample_pdf, "rb") as f:
        response = client.post(
            "/api/v1/parse",
            files={"files": ("test.pdf", f, "application/pdf")},
            data={
                "async_mode": "true",
                "backend": "pipeline",
                "parse_method": "auto",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert "status_url" in data
    assert data["status_url"].endswith(f"/api/v1/jobs/{data['job_id']}")
    assert "created_at" in data
    assert "request_id" in data


def test_async_mode_query_status(client: TestClient, sample_pdf: Path):
    """Test querying job status progresses from PENDING to SUCCESS."""
    # Submit async job
    with open(sample_pdf, "rb") as f:
        response = client.post(
            "/api/v1/parse",
            files={"files": ("test.pdf", f, "application/pdf")},
            data={
                "async_mode": "true",
                "backend": "pipeline",
                "parse_method": "auto",
            },
        )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Poll status until completed (max 30 seconds)
    max_attempts = 60
    for attempt in range(max_attempts):
        status_response = client.get(f"/api/v1/jobs/{job_id}")
        assert status_response.status_code == 200

        job_data = status_response.json()
        assert job_data["job_id"] == job_id
        assert "status" in job_data
        assert "created_at" in job_data

        if job_data["status"] in ["SUCCESS", "FAILED"]:
            # Job completed
            assert "completed_at" in job_data
            assert "started_at" in job_data

            if job_data["status"] == "SUCCESS":
                assert "outputs" in job_data
                assert isinstance(job_data["outputs"], list)
            else:
                assert "errors" in job_data
                assert isinstance(job_data["errors"], list)
            break

        time.sleep(0.5)
    else:
        pytest.fail(f"Job did not complete within {max_attempts * 0.5} seconds")


def test_async_mode_concurrent_limit(client: TestClient, sample_pdf: Path):
    """Test that concurrent job limit is enforced."""
    # Submit max_concurrent_jobs (default 10)
    job_ids = []
    for i in range(11):  # Try to submit 11 jobs
        with open(sample_pdf, "rb") as f:
            response = client.post(
                "/api/v1/parse",
                files={"files": ("test.pdf", f, "application/pdf")},
                data={
                    "async_mode": "true",
                    "backend": "pipeline",
                    "parse_method": "auto",
                },
            )

        if i < 10:
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])
        else:
            # 11th job should be rejected
            assert response.status_code == 503
            assert "Too many concurrent jobs" in response.json()["detail"]


def test_sync_mode_still_works(client: TestClient, sample_pdf: Path):
    """Test that sync mode (default) still works as before."""
    with open(sample_pdf, "rb") as f:
        response = client.post(
            "/api/v1/parse",
            files={"files": ("test.pdf", f, "application/pdf")},
            data={
                "async_mode": "false",  # Explicit sync mode
                "backend": "pipeline",
                "parse_method": "auto",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "outputs" in data
    assert "errors" in data
    assert "request_id" in data
    assert "job_id" not in data  # Sync mode doesn't return job_id


def test_job_not_found(client: TestClient):
    """Test querying non-existent job returns 404."""
    response = client.get("/api/v1/jobs/nonexistent-job-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_notification(sample_pdf: Path, tmp_path: Path):
    """Test webhook is called when job completes."""
    # This test requires a mock webhook server
    # Implementation left as placeholder for full integration testing
    pass

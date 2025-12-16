import asyncio
import os
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.main import create_app
from src.config.settings import get_settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture()
async def client(tmp_path: Path):
    # Point storage to a temp directory during tests
    os.environ["OUTPUT_BASE_PATH"] = str(tmp_path)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

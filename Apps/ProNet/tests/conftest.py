"""Pytest configuration and shared test fixtures for ProNet test suite."""
import os
import sys
import glob
from pathlib import Path
from typing import Dict, Generator, Any
import pytest

# Ensure backend directory is first in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "src" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Isolate database for tests using dedicated test database file
TEST_DB_PATH = BACKEND_DIR / "pronet_test.db"
os.environ["PRONET_DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["PRONET_ENV"] = "test"
os.environ["PRONET_UPLOAD_DIR"] = str(BACKEND_DIR / "uploads")

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Session-wide TestClient triggering app lifespan (migrations & deterministic seed)."""
    # Clean up any residual test database files prior to start
    for p in glob.glob(str(BACKEND_DIR / "pronet_test.db*")):
        try:
            os.remove(p)
        except OSError:
            pass

    with TestClient(app) as test_client:
        yield test_client

    # Teardown: clean up test database after session
    for p in glob.glob(str(BACKEND_DIR / "pronet_test.db*")):
        try:
            os.remove(p)
        except OSError:
            pass


@pytest.fixture(scope="session")
def tokens(client: TestClient) -> Dict[str, str]:
    """Cached authentication tokens for all 10 seeded personas."""
    personas = [
        "usr_elena_rostova",
        "usr_alex_chen",
        "usr_marcus_vance",
        "usr_priya_sharma",
        "usr_devon_taylor",
        "usr_sarah_jenkins",
        "usr_liam_patel",
        "usr_zack_kowalski",
        "usr_aisha_diop",
        "usr_jordan_mendez",
    ]
    token_map: Dict[str, str] = {}
    for user_id in personas:
        resp = client.post("/api/v1/auth/quick-switch", json={"user_id": user_id})
        if resp.status_code == 200:
            data = resp.json()
            token_map[user_id] = data["access_token"]
            # Short alias
            alias = user_id.replace("usr_", "")
            token_map[alias] = data["access_token"]
    return token_map


@pytest.fixture
def auth_headers():
    """Helper function yielding Authorization header dict."""
    def _headers(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    return _headers

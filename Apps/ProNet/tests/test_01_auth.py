"""Test Suite for Authentication and Persona Quick-Switching.

Coverage:
- REQ-001: Local Persona Quick-Switching (API-003, API-004)
- REQ-002: Standard Credential Authentication & Token Validation (API-001, API-002, API-005)
"""
import uuid
import pytest
from fastapi.testclient import TestClient


def test_req001_personas_list_happy_path(client: TestClient):
    """API-004 / REQ-001: Retrieve all 10 pre-seeded personas for quick-switcher UI."""
    response = client.get("/api/v1/auth/personas")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    personas = response.json()
    assert isinstance(personas, list)
    assert len(personas) == 10, f"Expected exactly 10 personas, found {len(personas)}"
    
    first = personas[0]
    for key in ("id", "email", "full_name", "headline"):
        assert key in first, f"Missing key {key} in persona payload"
    assert first["id"].startswith("usr_")


def test_req001_quick_switch_happy_path(client: TestClient):
    """API-003 / REQ-001: Instantaneous persona switch to Elena Rostova."""
    payload = {"user_id": "usr_elena_rostova"}
    response = client.post("/api/v1/auth/quick-switch", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"
    assert data["expires_in_seconds"] == 86400
    assert data["user"]["id"] == "usr_elena_rostova"
    assert data["user"]["full_name"] == "Elena Rostova"


def test_req001_quick_switch_negative_invalid_persona(client: TestClient):
    """API-003 / REQ-001: Persona switch fails for non-existent persona ID."""
    payload = {"user_id": "usr_invalid_ghost_999"}
    response = client.post("/api/v1/auth/quick-switch", json=payload)
    assert response.status_code == 404
    error = response.json().get("error", {})
    assert error.get("code") == "USER_NOT_FOUND"


def test_req002_register_happy_path(client: TestClient):
    """API-001 / REQ-002: User registration with valid unique credentials."""
    unique_email = f"qa_engineer_{uuid.uuid4().hex[:8]}@pronet.local"
    payload = {
        "email": unique_email,
        "password": "SecurePassword123!",
        "full_name": "Automation Tester",
        "headline": "Senior QA Automation Specialist",
        "location": "Seattle, WA",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["full_name"] == "Automation Tester"


def test_req002_register_negative_duplicate_email(client: TestClient):
    """API-001 / REQ-002: Registration fails when email already exists."""
    payload = {
        "email": "elena.rostova@pronet.local",
        "password": "AnotherPassword123!",
        "full_name": "Duplicate Elena",
        "headline": "Duplicate",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code in (409, 422)


def test_req002_register_negative_short_password(client: TestClient):
    """API-001 / REQ-002: Registration fails when password is shorter than 8 characters."""
    payload = {
        "email": f"short_pwd_{uuid.uuid4().hex[:6]}@pronet.local",
        "password": "short",
        "full_name": "Short Pwd",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_req002_login_happy_path(client: TestClient):
    """API-002 / REQ-002: Successful authentication with valid credentials."""
    # Seeded accounts have password "Password123!"
    payload = {
        "email": "elena.rostova@pronet.local",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == "usr_elena_rostova"


def test_req002_login_negative_invalid_password(client: TestClient):
    """API-002 / REQ-002: Login rejected on wrong password with ERR-001 INVALID_CREDENTIALS."""
    payload = {
        "email": "elena.rostova@pronet.local",
        "password": "IncorrectPassword999!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    error = response.json().get("error", {})
    assert error.get("code") == "INVALID_CREDENTIALS"


def test_req002_login_negative_nonexistent_email(client: TestClient):
    """API-002 / REQ-002: Login rejected for unregistered email."""
    payload = {
        "email": "nonexistent_ghost@pronet.local",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    error = response.json().get("error", {})
    assert error.get("code") == "INVALID_CREDENTIALS"


def test_req002_auth_me_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-005 / REQ-002: Retrieve current user identity via valid Bearer token."""
    token = tokens["usr_elena_rostova"]
    response = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["id"] == "usr_elena_rostova"
    assert data["email"] == "elena.rostova@pronet.local"
    assert "headline" in data
    assert "avatar_url" in data


def test_req002_auth_me_negative_missing_token(client: TestClient):
    """API-005 / REQ-002: Protected route returns 401 when Authorization header is omitted."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    error = response.json().get("error", {})
    assert error.get("code") in ("UNAUTHORIZED", "INVALID_TOKEN")


def test_req002_auth_me_negative_invalid_token(client: TestClient, auth_headers):
    """API-005 / REQ-002: Protected route returns 401 when token signature is corrupt."""
    bogus_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.bogus_payload.invalid_signature"
    response = client.get("/api/v1/auth/me", headers=auth_headers(bogus_token))
    assert response.status_code == 401
    error = response.json().get("error", {})
    assert error.get("code") in ("INVALID_TOKEN", "UNAUTHORIZED")

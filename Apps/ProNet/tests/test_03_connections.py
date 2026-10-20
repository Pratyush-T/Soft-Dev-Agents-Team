"""Test Suite for Connection Lifecycle & Social Graph Edge Management.

Coverage:
- REQ-005: Outgoing Connection Request Submission (API-020, EDG-001)
- REQ-006: Connection Request Acceptance and Ignorance (API-019, API-021, API-022)
- REQ-007: Outgoing Connection Request Cancellation (API-023)
- REQ-008: Connection Removal (Disconnect) (API-018, API-024)
- EDG-001: Reciprocal Collision Lock and Auto-Resolution
"""
import pytest
from fastapi.testclient import TestClient


def test_req005_send_connection_request_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-020 / REQ-005: User sends a connection request with an optional note."""
    # In seeded data, Zack Kowalski and Sarah Jenkins have no prior connection record.
    token = tokens["usr_zack_kowalski"]
    payload = {
        "recipient_id": "usr_sarah_jenkins",
        "note": "Hi Sarah, would love to connect and discuss streaming data architectures!",
    }
    resp = client.post("/api/v1/connections/request", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["initiator_id"] == "usr_zack_kowalski"
    assert data["recipient_id"] == "usr_sarah_jenkins"
    assert data["status"] == "PENDING"
    assert data["note"] == payload["note"]


def test_req005_send_connection_request_negative_duplicate(client: TestClient, tokens: dict, auth_headers):
    """API-020 / REQ-005: Sending a duplicate connection request returns 409 CONNECTION_ALREADY_REQUESTED."""
    token = tokens["usr_zack_kowalski"]
    payload = {
        "recipient_id": "usr_sarah_jenkins",
        "note": "Second attempt to connect.",
    }
    resp = client.post("/api/v1/connections/request", json=payload, headers=auth_headers(token))
    assert resp.status_code == 409
    error = resp.json().get("error", {})
    assert error.get("code") == "CONNECTION_ALREADY_REQUESTED"


def test_req005_send_connection_request_negative_already_connected(client: TestClient, tokens: dict, auth_headers):
    """API-020 / REQ-005: Sending request to an existing 1st-degree connection returns 409 ALREADY_CONNECTED."""
    # Elena and Alex are already 1st degree (conn_01)
    token = tokens["usr_elena_rostova"]
    payload = {"recipient_id": "usr_alex_chen", "note": "Reconnecting"}
    resp = client.post("/api/v1/connections/request", json=payload, headers=auth_headers(token))
    assert resp.status_code == 409
    error = resp.json().get("error", {})
    assert error.get("code") == "ALREADY_CONNECTED"


def test_req005_send_connection_request_negative_self_connection(client: TestClient, tokens: dict, auth_headers):
    """API-020 / REQ-005: Attempting to connect to self returns 422 SELF_CONNECTION_FORBIDDEN."""
    token = tokens["usr_elena_rostova"]
    payload = {"recipient_id": "usr_elena_rostova", "note": "Self connect"}
    resp = client.post("/api/v1/connections/request", json=payload, headers=auth_headers(token))
    assert resp.status_code == 422
    error = resp.json().get("error", {})
    assert error.get("code") == "SELF_CONNECTION_FORBIDDEN"


def test_req005_reciprocal_collision_autoresolve_edg001(client: TestClient, tokens: dict, auth_headers):
    """API-020 / REQ-005 / EDG-001: Reciprocal Collision Lock Auto-Resolves to ACCEPTED.
    
    Seeded edge conn_14: Aisha Diop sent PENDING request to Elena Rostova.
    When Elena Rostova sends a connection request to Aisha Diop, the collision guard
    detects the existing pending request, transitions edge to ACCEPTED, and increments counts.
    """
    token_elena = tokens["usr_elena_rostova"]
    payload = {
        "recipient_id": "usr_aisha_diop",
        "note": "Aisha, thrilled to connect!",
    }
    resp = client.post("/api/v1/connections/request", json=payload, headers=auth_headers(token_elena))
    # Collision auto-resolve returns 201 or 200 with status ACCEPTED
    assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["status"] == "ACCEPTED", f"Expected auto-resolution to ACCEPTED, got {data['status']}"

    # Verify both are now 1st degree
    profile_resp = client.get("/api/v1/users/usr_aisha_diop", headers=auth_headers(token_elena))
    assert profile_resp.status_code == 200
    assert profile_resp.json()["degree"] == "1st"


def test_req006_list_pending_connections_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-019 / REQ-006: Retrieve incoming and outgoing pending connection requests."""
    # conn_13: Elena Rostova sent PENDING request to Sarah Jenkins in seed
    token_sarah = tokens["usr_sarah_jenkins"]
    resp = client.get("/api/v1/connections/pending", headers=auth_headers(token_sarah))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "incoming" in data
    assert "outgoing" in data
    
    incoming_ids = [c["id"] for c in data["incoming"]]
    assert "conn_13" in incoming_ids


def test_req006_accept_incoming_request_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-021 / REQ-006: Recipient accepts pending request; status becomes ACCEPTED."""
    token_sarah = tokens["usr_sarah_jenkins"]
    resp = client.post("/api/v1/connections/conn_13/accept", headers=auth_headers(token_sarah))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["id"] == "conn_13"
    assert data["status"] == "ACCEPTED"


def test_req006_ignore_incoming_request_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-022 / REQ-006: Recipient ignores incoming connection request."""
    # Let Jordan Mendez send request to Marcus Vance
    token_jordan = tokens["usr_jordan_mendez"]
    token_marcus = tokens["usr_marcus_vance"]

    req_resp = client.post(
        "/api/v1/connections/request",
        json={"recipient_id": "usr_marcus_vance", "note": "Connecting for security reviews"},
        headers=auth_headers(token_jordan)
    )
    assert req_resp.status_code == 201
    conn_id = req_resp.json()["id"]

    # Marcus Vance ignores the request
    ignore_resp = client.post(f"/api/v1/connections/{conn_id}/ignore", headers=auth_headers(token_marcus))
    assert ignore_resp.status_code == 200
    assert ignore_resp.json()["status"] == "IGNORED"


def test_req006_accept_negative_not_recipient(client: TestClient, tokens: dict, auth_headers):
    """API-021 / REQ-006: Non-recipient cannot accept a connection request."""
    # Create request from Marcus to Chloe
    token_marcus = tokens["usr_marcus_vance"]
    token_priya = tokens["usr_priya_sharma"]
    
    # Send request from Marcus to Devon Taylor
    req_resp = client.post(
        "/api/v1/connections/request",
        json={"recipient_id": "usr_devon_taylor", "note": "Sync"},
        headers=auth_headers(token_marcus)
    )
    if req_resp.status_code == 201:
        conn_id = req_resp.json()["id"]
        # Priya Sharma (unrelated party) attempts to accept it
        resp = client.post(f"/api/v1/connections/{conn_id}/accept", headers=auth_headers(token_priya))
        assert resp.status_code in (403, 404)


def test_req006_accept_negative_nonexistent_connection(client: TestClient, tokens: dict, auth_headers):
    """API-021 / REQ-006: Accepting non-existent connection returns 404."""
    token = tokens["usr_elena_rostova"]
    resp = client.post("/api/v1/connections/conn_ghost_999/accept", headers=auth_headers(token))
    assert resp.status_code == 404


def test_req007_withdraw_pending_request_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-023 / REQ-007: Initiator withdraws a pending request; record is removed."""
    token_devon = tokens["usr_devon_taylor"]
    # Devon sends request to Zack
    req = client.post(
        "/api/v1/connections/request",
        json={"recipient_id": "usr_zack_kowalski", "note": "Withdraw test"},
        headers=auth_headers(token_devon)
    )
    assert req.status_code == 201
    conn_id = req.json()["id"]

    # Devon withdraws the request
    del_resp = client.delete(f"/api/v1/connections/{conn_id}/withdraw", headers=auth_headers(token_devon))
    assert del_resp.status_code == 204

    # Verify withdraw again fails with 404
    del_resp_again = client.delete(f"/api/v1/connections/{conn_id}/withdraw", headers=auth_headers(token_devon))
    assert del_resp_again.status_code == 404


def test_req007_withdraw_negative_already_accepted(client: TestClient, tokens: dict, auth_headers):
    """API-023 / REQ-007: Withdrawing an already ACCEPTED connection returns 400 CANNOT_WITHDRAW_ACCEPTED_CONNECTION."""
    token_elena = tokens["usr_elena_rostova"]
    # conn_01 is ACCEPTED between Elena and Alex
    resp = client.delete("/api/v1/connections/conn_01/withdraw", headers=auth_headers(token_elena))
    assert resp.status_code == 400
    error = resp.json().get("error", {})
    assert error.get("code") == "CANNOT_WITHDRAW_ACCEPTED_CONNECTION"


def test_req008_list_confirmed_connections_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-018 / REQ-008: Retrieve active 1st-degree connections for user."""
    token_elena = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/connections", headers=auth_headers(token_elena))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    conns = resp.json()
    assert isinstance(conns, list)
    assert len(conns) >= 1
    # Check Alex Chen is among the connections
    peer_ids = [c["peer"]["id"] for c in conns]
    assert "usr_alex_chen" in peer_ids


def test_req008_disconnect_peer_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-024 / REQ-008: Disconnect an active 1st-degree connection."""
    # In seeded data, conn_09 is ACCEPTED between Priya Sharma and Devon Taylor
    token_priya = tokens["usr_priya_sharma"]
    resp = client.delete("/api/v1/connections/usr_devon_taylor", headers=auth_headers(token_priya))
    assert resp.status_code == 204

    # Verify they are no longer 1st degree
    profile_resp = client.get("/api/v1/users/usr_devon_taylor", headers=auth_headers(token_priya))
    assert profile_resp.status_code == 200
    assert profile_resp.json()["connection_status_with_viewer"] in ("NONE", "IGNORED")


def test_req008_disconnect_negative_not_connected(client: TestClient, tokens: dict, auth_headers):
    """API-024 / REQ-008: Disconnecting a user with no connection record returns 404."""
    token_elena = tokens["usr_elena_rostova"]
    resp = client.delete("/api/v1/connections/usr_jordan_mendez", headers=auth_headers(token_elena))
    assert resp.status_code == 404

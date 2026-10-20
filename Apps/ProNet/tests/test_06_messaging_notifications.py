"""Test Suite for Direct Messaging, WebSockets, and Notification Dispatch.

Coverage:
- REQ-017: Real-Time Direct Messaging (API-042, API-043, API-044, /ws, EDG-002)
- REQ-018: Real-Time Notification Dispatch & Unread Badges (API-045, API-046, API-047)
"""
import json
import pytest
from fastapi.testclient import TestClient


def test_req017_list_conversations_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-042 / REQ-017: List conversation summaries with most recent message and unread count."""
    token_elena = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/messages/conversations", headers=auth_headers(token_elena))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    convs = resp.json()
    assert isinstance(convs, list)
    assert len(convs) >= 1
    # Check Alex Chen is in conversations
    peer_ids = [c["peer"]["id"] for c in convs]
    assert "usr_alex_chen" in peer_ids
    alex_conv = next(c for c in convs if c["peer"]["id"] == "usr_alex_chen")
    assert "last_message" in alex_conv
    assert "unread_count" in alex_conv


def test_req017_message_history_1st_degree_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-043 / REQ-017: Retrieve message history with confirmed 1st-degree connection."""
    token_elena = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/messages/usr_alex_chen", headers=auth_headers(token_elena))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "items" in data
    messages = data["items"]
    assert len(messages) >= 1
    assert all("content" in m for m in messages)


def test_req017_message_history_negative_non_1st_degree_edg002(client: TestClient, tokens: dict, auth_headers):
    """API-043 / REQ-017 / EDG-002: Accessing message history with non-1st-degree connection returns 403 MUST_BE_FIRST_DEGREE."""
    token_elena = tokens["usr_elena_rostova"]
    # Jordan Mendez is not connected to Elena
    resp = client.get("/api/v1/messages/usr_jordan_mendez", headers=auth_headers(token_elena))
    assert resp.status_code == 403
    error = resp.json().get("error", {})
    assert error.get("code") == "MUST_BE_FIRST_DEGREE"


def test_req017_mark_conversation_read_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-044 / REQ-017: Mark incoming messages from a peer as read."""
    token_elena = tokens["usr_elena_rostova"]
    resp = client.post("/api/v1/messages/usr_alex_chen/read", headers=auth_headers(token_elena))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "marked_count" in data
    assert isinstance(data["marked_count"], int)


def test_req017_websocket_live_direct_message_happy_path(client: TestClient, tokens: dict):
    """REQ-017 / WebSocket: Message dispatch and acknowledgment over persistent WebSocket."""
    token_elena = tokens["usr_elena_rostova"]

    with client.websocket_connect(f"/ws?token={token_elena}") as ws_elena:
        welcome_elena = ws_elena.receive_json()
        assert welcome_elena["type"] == "CONNECTED"
        assert welcome_elena["user_id"] == "usr_elena_rostova"

        # Elena sends PING
        ws_elena.send_text(json.dumps({"type": "PING"}))
        pong = ws_elena.receive_json()
        assert pong["type"] == "PONG"

        # Elena sends message to confirmed 1st degree peer Alex
        dm_payload = {
            "type": "SEND_MESSAGE",
            "recipient_id": "usr_alex_chen",
            "content": "Hello Alex! Verifying WebSocket transport delivery.",
        }
        ws_elena.send_text(json.dumps(dm_payload))

        # Elena receives ACK
        ack_elena = ws_elena.receive_json()
        assert ack_elena["type"] == "MESSAGE_ACK"
        assert ack_elena["recipient_id"] == "usr_alex_chen"
        assert "message_id" in ack_elena


def test_req017_websocket_negative_non_1st_degree(client: TestClient, tokens: dict):
    """REQ-017 / EDG-002: Sending WebSocket message to non-1st-degree connection returns error frame."""
    token_elena = tokens["usr_elena_rostova"]

    with client.websocket_connect(f"/ws?token={token_elena}") as ws_elena:
        ws_elena.receive_json()  # welcome

        # Attempt to message unconnected user Jordan Mendez
        illegal_payload = {
            "type": "SEND_MESSAGE",
            "recipient_id": "usr_jordan_mendez",
            "content": "This transmission should be rejected.",
        }
        ws_elena.send_text(json.dumps(illegal_payload))

        err_frame = ws_elena.receive_json()
        assert err_frame["type"] == "ERROR"
        assert err_frame["code"] == "MUST_BE_FIRST_DEGREE_CONNECTION"


def test_req017_websocket_negative_unauthorized_token(client: TestClient):
    """REQ-017: Connecting to WebSocket with invalid token closes socket with code 4001."""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=invalid_tampered_token") as ws:
            ws.receive_json()


def test_req018_list_notifications_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-045 / REQ-018: Retrieve paginated notifications for current user."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/notifications", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "items" in data
    notifs = data["items"]
    assert isinstance(notifs, list)


def test_req018_get_badge_counts_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-047 / REQ-018: Retrieve live badge counters for top navbar."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/notifications/badges", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    badges = resp.json()
    for field in ("unread_messages", "pending_connections", "unread_notifications"):
        assert field in badges
        assert isinstance(badges[field], int)
        assert badges[field] >= 0


def test_req018_mark_notifications_read_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-046 / REQ-018: Mark all notifications as read."""
    token = tokens["usr_elena_rostova"]
    resp = client.post("/api/v1/notifications/read", json={}, headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    assert "marked_count" in data

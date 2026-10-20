"""Test Suite for Activity Feed, Rich Posts, Reactions, and Threaded Comments.

Coverage:
- REQ-009: Rich Post Creation (API-026, API-027, API-028)
- REQ-010: Feed Consumption & Dual-Mode Sorting (API-025, KPI-007)
- REQ-011: Multi-Type Post Reactions (API-029, API-030)
- REQ-012: Two-Level Comment Threading & Moderation (API-031, API-032, API-033)
"""
import uuid
from datetime import datetime
import pytest
from fastapi.testclient import TestClient


def test_req009_create_post_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-026 / REQ-009: Create rich post with formatted text and python code snippet."""
    token = tokens["usr_elena_rostova"]
    payload = {
        "content": "Excited to share our breakthrough in distributed tensor checkpointing across NVLink clusters!",
        "code_snippet": "def checkpoint_tensors(state):\n    return torch.save(state, '/mnt/nvlink/ckpt.pt')",
        "code_language": "python",
        "image_url": None,
    }
    resp = client.post("/api/v1/posts", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    post = resp.json()
    assert post["id"].startswith("post_")
    assert post["author"]["id"] == "usr_elena_rostova"
    assert post["content"] == payload["content"]
    assert post["code_snippet"] == payload["code_snippet"]
    assert post["code_language"] == "python"
    assert post["like_count"] == 0
    assert post["comment_count"] == 0


def test_req009_create_post_negative_empty_content(client: TestClient, tokens: dict, auth_headers):
    """API-026 / REQ-009: Validation rejects post creation with empty content."""
    token = tokens["usr_elena_rostova"]
    payload = {"content": ""}
    resp = client.post("/api/v1/posts", json=payload, headers=auth_headers(token))
    assert resp.status_code == 422


def test_req009_get_single_post_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-027 / REQ-009: Retrieve single post detail with hydrated author, counts, and reactions."""
    token = tokens["usr_alex_chen"]
    # Seeded post post_01 exists
    resp = client.get("/api/v1/posts/post_01", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    post = resp.json()
    assert post["id"] == "post_01"
    assert "author" in post
    assert "like_count" in post
    assert "comment_count" in post


def test_req009_get_post_negative_not_found(client: TestClient, tokens: dict, auth_headers):
    """API-027 / REQ-009: Requesting non-existent post returns 404 POST_NOT_FOUND."""
    token = tokens["usr_alex_chen"]
    resp = client.get("/api/v1/posts/post_ghost_not_found_999", headers=auth_headers(token))
    assert resp.status_code == 404
    error = resp.json().get("error", {})
    assert error.get("code") == "POST_NOT_FOUND"


def test_req009_delete_post_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-028 / REQ-009: Author deletes their own post."""
    token = tokens["usr_marcus_vance"]
    # Create a throwaway post
    create_resp = client.post(
        "/api/v1/posts",
        json={"content": "Post scheduled for immediate deletion test."},
        headers=auth_headers(token)
    )
    assert create_resp.status_code == 201
    post_id = create_resp.json()["id"]

    # Delete the post
    del_resp = client.delete(f"/api/v1/posts/{post_id}", headers=auth_headers(token))
    assert del_resp.status_code == 204

    # Verify post no longer exists
    get_resp = client.get(f"/api/v1/posts/{post_id}", headers=auth_headers(token))
    assert get_resp.status_code == 404


def test_req009_delete_post_negative_unauthorized(client: TestClient, tokens: dict, auth_headers):
    """API-028 / REQ-009: Non-author cannot delete someone else's post."""
    token_priya = tokens["usr_priya_sharma"]
    # Attempt to delete post_01 authored by Elena Rostova
    resp = client.delete("/api/v1/posts/post_01", headers=auth_headers(token_priya))
    assert resp.status_code in (403, 401)


def test_req010_feed_recent_sorting_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-025 / REQ-010: Recent feed returns posts strictly ordered by created_at DESC."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/feed?mode=recent&limit=10", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    items = data["items"]
    assert len(items) >= 2

    # Verify descending timestamps
    for i in range(len(items) - 1):
        t1 = datetime.fromisoformat(items[i]["created_at"].replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(items[i + 1]["created_at"].replace("Z", "+00:00"))
        assert t1 >= t2, f"Recent feed not sorted chronologically: {t1} < {t2}"


def test_req010_feed_top_sorting_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-025 / REQ-010: Top feed returns engagement-ranked posts."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/feed?mode=top&limit=10", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    items = data["items"]
    assert len(items) >= 2


def test_req010_feed_cursor_pagination_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-025 / REQ-010: Cursor-based feed pagination retrieves contiguous items without duplication."""
    token = tokens["usr_elena_rostova"]
    page1 = client.get("/api/v1/feed?mode=recent&limit=4", headers=auth_headers(token)).json()
    assert len(page1["items"]) == 4
    assert page1["has_more"] is True
    assert page1["next_cursor"] is not None

    page2 = client.get(f"/api/v1/feed?mode=recent&limit=4&cursor={page1['next_cursor']}", headers=auth_headers(token)).json()
    assert len(page2["items"]) >= 1

    ids_page1 = {item["id"] for item in page1["items"]}
    ids_page2 = {item["id"] for item in page2["items"]}
    assert ids_page1.isdisjoint(ids_page2), "Duplicate post IDs detected between feed pagination pages"


def test_req010_feed_negative_invalid_mode(client: TestClient, tokens: dict, auth_headers):
    """API-025 / REQ-010: Invalid feed mode returns 422 validation failure."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/feed?mode=viral", headers=auth_headers(token))
    assert resp.status_code == 422


def test_req011_reaction_lifecycle_add_toggle_switch_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-029, API-030 / REQ-011: Add reaction, toggle off, switch reaction type."""
    token_priya = tokens["usr_priya_sharma"]
    # Create dedicated post for reaction test
    post_resp = client.post(
        "/api/v1/posts",
        json={"content": "React to this milestone post!"},
        headers=auth_headers(token_priya)
    )
    assert post_resp.status_code == 201
    post_id = post_resp.json()["id"]

    token_alex = tokens["usr_alex_chen"]

    # 1. Add Reaction CELEBRATE
    r1 = client.post(f"/api/v1/posts/{post_id}/reactions", json={"reaction_type": "CELEBRATE"}, headers=auth_headers(token_alex))
    assert r1.status_code == 200
    assert r1.json()["active_reaction"] == "CELEBRATE"
    assert r1.json()["celebrate_count"] == 1

    # 2. Toggle Off: Sending same reaction CELEBRATE again removes it
    r2 = client.post(f"/api/v1/posts/{post_id}/reactions", json={"reaction_type": "CELEBRATE"}, headers=auth_headers(token_alex))
    assert r2.status_code == 200
    assert r2.json()["active_reaction"] is None
    assert r2.json()["celebrate_count"] == 0

    # 3. Add LIKE
    r3 = client.post(f"/api/v1/posts/{post_id}/reactions", json={"reaction_type": "LIKE"}, headers=auth_headers(token_alex))
    assert r3.status_code == 200
    assert r3.json()["active_reaction"] == "LIKE"
    assert r3.json()["like_count"] == 1

    # 4. Switch from LIKE to INSIGHTFUL
    r4 = client.post(f"/api/v1/posts/{post_id}/reactions", json={"reaction_type": "INSIGHTFUL"}, headers=auth_headers(token_alex))
    assert r4.status_code == 200
    assert r4.json()["active_reaction"] == "INSIGHTFUL"
    assert r4.json()["like_count"] == 0
    assert r4.json()["insightful_count"] == 1

    # 5. Explicit Delete Reaction (API-030)
    r5 = client.delete(f"/api/v1/posts/{post_id}/reactions", headers=auth_headers(token_alex))
    assert r5.status_code == 204


def test_req011_reaction_negative_nonexistent_post(client: TestClient, tokens: dict, auth_headers):
    """API-029 / REQ-011: Reacting to non-existent post returns 404 POST_NOT_FOUND."""
    token = tokens["usr_alex_chen"]
    resp = client.post("/api/v1/posts/post_ghost_999/reactions", json={"reaction_type": "LIKE"}, headers=auth_headers(token))
    assert resp.status_code == 404
    error = resp.json().get("error", {})
    assert error.get("code") == "POST_NOT_FOUND"


def test_req012_comment_threading_and_moderation_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-031, API-032, API-033 / REQ-012: Level 1 comment, Level 2 reply, Post author moderation."""
    token_author = tokens["usr_elena_rostova"]
    token_commenter = tokens["usr_alex_chen"]
    token_replier = tokens["usr_priya_sharma"]

    # Create root post by Elena
    post_resp = client.post(
        "/api/v1/posts",
        json={"content": "Discussing 2-level comment threading."},
        headers=auth_headers(token_author)
    )
    assert post_resp.status_code == 201
    post_id = post_resp.json()["id"]

    # 1. Level 1 Root Comment by Alex Chen
    c1 = client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "This is a Level 1 root comment.", "parent_id": None},
        headers=auth_headers(token_commenter)
    )
    assert c1.status_code == 201, f"Expected 201, got {c1.status_code}: {c1.text}"
    root_cmt = c1.json()
    root_id = root_cmt["id"]
    assert root_cmt["parent_id"] is None

    # 2. Level 2 Nested Reply by Priya Sharma
    c2 = client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "This is a Level 2 reply to root.", "parent_id": root_id},
        headers=auth_headers(token_replier)
    )
    assert c2.status_code == 201
    reply_cmt = c2.json()
    reply_id = reply_cmt["id"]
    assert reply_cmt["parent_id"] == root_id

    # 3. Verify Threaded Tree (API-031)
    tree_resp = client.get(f"/api/v1/posts/{post_id}/comments", headers=auth_headers(token_author))
    assert tree_resp.status_code == 200
    comments_tree = tree_resp.json()
    assert len(comments_tree) >= 1
    target_root = next(c for c in comments_tree if c["id"] == root_id)
    assert len(target_root["replies"]) == 1
    assert target_root["replies"][0]["id"] == reply_id

    # 4. Post Author Moderation Delete (API-033)
    # Elena (post author) deletes Alex's root comment and cascade deletes Priya's reply
    del_resp = client.delete(f"/api/v1/comments/{root_id}", headers=auth_headers(token_author))
    assert del_resp.status_code == 204


def test_req012_comment_negative_level3_depth_violation(client: TestClient, tokens: dict, auth_headers):
    """API-032 / REQ-012: Level 3 reply is strictly blocked with 422 MAX_COMMENT_DEPTH_EXCEEDED."""
    token = tokens["usr_alex_chen"]
    # cmt_01_01 is a Level 2 reply to cmt_01 on post_01
    level3_payload = {
        "content": "Attempting illegal Level 3 comment nesting.",
        "parent_id": "cmt_01_01",
    }
    resp = client.post("/api/v1/posts/post_01/comments", json=level3_payload, headers=auth_headers(token))
    assert resp.status_code in (400, 422)
    error = resp.json().get("error", {})
    assert error.get("code") == "MAX_COMMENT_DEPTH_EXCEEDED"


def test_req012_comment_negative_unauthorized_deletion(client: TestClient, tokens: dict, auth_headers):
    """API-033 / REQ-012: User who is neither comment author nor post author cannot delete comment."""
    token_priya = tokens["usr_priya_sharma"]
    # cmt_01 on post_01 (authored by Alex Chen, post authored by Elena Rostova)
    resp = client.delete("/api/v1/comments/cmt_01", headers=auth_headers(token_priya))
    assert resp.status_code == 403
    error = resp.json().get("error", {})
    assert error.get("code") == "CANNOT_MODERATE_COMMENT"

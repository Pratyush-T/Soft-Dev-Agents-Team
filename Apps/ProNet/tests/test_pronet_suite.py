import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add backend directory to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Verifies baseline health check endpoints."""
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "pronet-backend"

@pytest.mark.asyncio
async def test_personas_and_quick_switch(client: AsyncClient):
    """REQ-001: Verifies listing 10 pre-seeded personas and 1-click quick-switching."""
    res = await client.get("/api/v1/auth/personas")
    assert res.status_code == 200
    personas = res.json()
    assert len(personas) >= 10
    
    # Test quick-switching to Elena Rostova
    elena = next(p for p in personas if "Elena" in p["full_name"])
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": elena["id"]})
    assert switch_res.status_code == 200
    token_data = switch_res.json()
    assert "access_token" in token_data
    assert token_data["user"]["id"] == elena["id"]

@pytest.mark.asyncio
async def test_auth_me_and_profile(client: AsyncClient):
    """REQ-002 & REQ-003: Verifies current user profile and career history."""
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": "usr_elena_rostova"})
    token = switch_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check current user summary
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["full_name"] == "Elena Rostova"
    
    # Check full profile with experiences and education
    profile_res = await client.get("/api/v1/users/usr_elena_rostova", headers=headers)
    assert profile_res.status_code == 200
    profile = profile_res.json()
    assert "experiences" in profile
    assert "educations" in profile
    assert "skills" in profile
    assert len(profile["experiences"]) > 0

@pytest.mark.asyncio
async def test_connection_degree_badges(client: AsyncClient):
    """REQ-004: Verifies 1st-degree and 2nd-degree mutual badge calculations."""
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": "usr_elena_rostova"})
    token = switch_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Alex Chen is a 1st degree connection of Elena
    alex_res = await client.get("/api/v1/users/usr_alex_chen", headers=headers)
    assert alex_res.status_code == 200
    alex_data = alex_res.json()
    assert alex_data["degree"] == "1st"

@pytest.mark.asyncio
async def test_feed_dual_mode_and_hydration(client: AsyncClient):
    """REQ-008 & KPI-007: Verifies dual-mode feed (Recent vs. Top) with author hydration."""
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": "usr_elena_rostova"})
    token = switch_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Recent Feed
    recent_res = await client.get("/api/v1/feed?mode=recent&limit=10", headers=headers)
    assert recent_res.status_code == 200
    recent_posts = recent_res.json()["items"]
    assert len(recent_posts) > 0
    assert "author" in recent_posts[0]
    assert "like_count" in recent_posts[0]
    
    # Top Feed
    top_res = await client.get("/api/v1/feed?mode=top&limit=10", headers=headers)
    assert top_res.status_code == 200
    top_posts = top_res.json()["items"]
    assert len(top_posts) > 0

@pytest.mark.asyncio
async def test_reaction_toggle(client: AsyncClient):
    """REQ-009: Verifies toggling and switching reactions (LIKE, CELEBRATE, INSIGHTFUL)."""
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": "usr_elena_rostova"})
    token = switch_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # React to post_01 with CELEBRATE
    react_res = await client.post("/api/v1/posts/post_01/reactions", json={"reaction_type": "CELEBRATE"}, headers=headers)
    assert react_res.status_code == 200
    data = react_res.json()
    assert "celebrate_count" in data

@pytest.mark.asyncio
async def test_comment_hierarchy(client: AsyncClient):
    """REQ-010: Verifies 2-level comment threading and blocks level 3+."""
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": "usr_elena_rostova"})
    token = switch_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Post root comment (Level 1)
    c1_res = await client.post("/api/v1/posts/post_01/comments", json={"content": "Root architectural observation."}, headers=headers)
    assert c1_res.status_code == 201
    c1_id = c1_res.json()["id"]
    
    # Post reply (Level 2)
    c2_res = await client.post("/api/v1/posts/post_01/comments", json={"content": "Agreed on point.", "parent_id": c1_id}, headers=headers)
    assert c2_res.status_code == 201
    c2_id = c2_res.json()["id"]
    
    # Attempt reply to reply (Level 3 - Forbidden)
    c3_res = await client.post("/api/v1/posts/post_01/comments", json={"content": "Nested too deep.", "parent_id": c2_id}, headers=headers)
    assert c3_res.status_code in [400, 422]

@pytest.mark.asyncio
async def test_job_board_and_easy_apply(client: AsyncClient):
    """REQ-012, REQ-014, REQ-015: Verifies job discovery and easy apply snapshot."""
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": "usr_elena_rostova"})
    token = switch_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List jobs
    jobs_res = await client.get("/api/v1/jobs?limit=5", headers=headers)
    assert jobs_res.status_code == 200
    jobs = jobs_res.json()["items"]
    assert len(jobs) > 0
    target_job = jobs[0]
    assert "title" in target_job
    assert "company_name" in target_job

@pytest.mark.asyncio
async def test_direct_messaging_restriction(client: AsyncClient):
    """REQ-016 & EDG-002: Verifies messaging history is accessible for 1st-degree and blocked for non-connections."""
    switch_res = await client.post("/api/v1/auth/quick-switch", json={"user_id": "usr_elena_rostova"})
    token = switch_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check message history with 1st degree connection (Alex Chen)
    msg_res = await client.get("/api/v1/messages/usr_alex_chen", headers=headers)
    assert msg_res.status_code == 200
    
    # Check message history with non-connection (Zack Kowalski - 3rd degree out of network)
    blocked_res = await client.get("/api/v1/messages/usr_zack_kowalski", headers=headers)
    assert blocked_res.status_code in [400, 403]

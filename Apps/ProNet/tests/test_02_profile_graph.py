"""Test Suite for Professional Profile & Degree Graph Evaluation.

Coverage:
- REQ-003: Professional Profile Editing (API-007, API-009, API-010, API-011, API-012, API-013, API-014, API-015, API-016, API-017)
- REQ-004: Degree Calculation and Badge Display (API-006, API-008)
"""
import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient


def test_req003_get_my_profile_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-007 / REQ-003: Get current user's profile attributes."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/users/me/profile", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["user_id"] == "usr_elena_rostova"
    assert "headline" in data
    assert "location" in data


def test_req003_update_profile_attributes_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-007 / REQ-003: Update headline, bio, and location."""
    token = tokens["usr_elena_rostova"]
    new_headline = "Principal AI Systems Architect | Core Optimization"
    new_location = "San Francisco Bay Area, CA"
    new_bio = "Building high-performance distributed AI training infrastructure with WAL SQLite."
    
    patch_payload = {
        "headline": new_headline,
        "location": new_location,
        "bio": new_bio,
    }
    resp = client.patch("/api/v1/users/me/profile", json=patch_payload, headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["headline"] == new_headline
    assert data["location"] == new_location
    assert data["bio"] == new_bio


def test_req003_experience_lifecycle_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-009, API-010, API-011 / REQ-003: Add, update, and delete work experience."""
    token = tokens["usr_alex_chen"]
    
    # 1. Add Experience (API-009)
    exp_payload = {
        "company": "Apex Cloud Infrastructure",
        "title": "Lead Cloud Infrastructure Architect",
        "location": "Seattle, WA",
        "start_date": "2023-01-01",
        "end_date": None,
        "is_current": True,
        "description": "Leading Kubernetes and multi-region network architectures.",
    }
    create_resp = client.post("/api/v1/users/me/experiences", json=exp_payload, headers=auth_headers(token))
    assert create_resp.status_code == 201, f"Expected 201, got {create_resp.status_code}: {create_resp.text}"
    exp = create_resp.json()
    exp_id = exp["id"]
    assert exp["company"] == "Apex Cloud Infrastructure"
    assert exp["is_current"] is True

    # 2. Update Experience (API-010)
    update_payload = {
        "company": "Apex Cloud Systems",
        "title": "VP of Cloud Architecture",
        "location": "Remote, WA",
        "start_date": "2023-01-01",
        "end_date": None,
        "is_current": True,
        "description": "Promoted to VP of Cloud Architecture.",
    }
    update_resp = client.put(f"/api/v1/users/me/experiences/{exp_id}", json=update_payload, headers=auth_headers(token))
    assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}: {update_resp.text}"
    assert update_resp.json()["title"] == "VP of Cloud Architecture"

    # 3. Delete Experience (API-011)
    del_resp = client.delete(f"/api/v1/users/me/experiences/{exp_id}", headers=auth_headers(token))
    assert del_resp.status_code == 204

    # 4. Verify Not Found on subsequent update
    check_resp = client.put(f"/api/v1/users/me/experiences/{exp_id}", json=update_payload, headers=auth_headers(token))
    assert check_resp.status_code == 404


def test_req003_experience_negative_end_before_start(client: TestClient, tokens: dict, auth_headers):
    """API-009 / REQ-003: Negative path: end_date earlier than start_date returns 422 END_DATE_BEFORE_START_DATE."""
    token = tokens["usr_alex_chen"]
    invalid_exp = {
        "company": "Time Paradox Labs",
        "title": "Quantum Systems Engineer",
        "location": "Palo Alto, CA",
        "start_date": "2024-05-01",
        "end_date": "2022-01-01",
        "is_current": False,
        "description": "Invalid inverted date range.",
    }
    resp = client.post("/api/v1/users/me/experiences", json=invalid_exp, headers=auth_headers(token))
    assert resp.status_code == 422
    error = resp.json().get("error", {})
    assert error.get("code") == "END_DATE_BEFORE_START_DATE"


def test_req003_education_lifecycle_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-012, API-013, API-014 / REQ-003: Add, update, and delete education history."""
    token = tokens["usr_alex_chen"]

    # 1. Add Education (API-012)
    edu_payload = {
        "institution": "University of Washington",
        "degree": "M.S.",
        "field_of_study": "Computer Science & Distributed Systems",
        "start_year": 2016,
        "end_year": 2018,
    }
    resp = client.post("/api/v1/users/me/educations", json=edu_payload, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    edu = resp.json()
    edu_id = edu["id"]
    assert edu["degree"] == "M.S."

    # 2. Update Education (API-013)
    update_payload = {
        "institution": "University of Washington",
        "degree": "Ph.D.",
        "field_of_study": "Distributed Systems",
        "start_year": 2016,
        "end_year": 2021,
    }
    up_resp = client.put(f"/api/v1/users/me/educations/{edu_id}", json=update_payload, headers=auth_headers(token))
    assert up_resp.status_code == 200
    assert up_resp.json()["degree"] == "Ph.D."

    # 3. Delete Education (API-014)
    del_resp = client.delete(f"/api/v1/users/me/educations/{edu_id}", headers=auth_headers(token))
    assert del_resp.status_code == 204


def test_req003_education_negative_end_before_start(client: TestClient, tokens: dict, auth_headers):
    """API-012 / REQ-003: Negative path: end_year earlier than start_year returns 422."""
    token = tokens["usr_alex_chen"]
    invalid_edu = {
        "institution": "Inverted Time Academy",
        "degree": "B.S.",
        "field_of_study": "History",
        "start_year": 2020,
        "end_year": 2015,
    }
    resp = client.post("/api/v1/users/me/educations", json=invalid_edu, headers=auth_headers(token))
    assert resp.status_code == 422
    error = resp.json().get("error", {})
    assert error.get("code") == "END_DATE_BEFORE_START_DATE"


def test_req003_skills_search_and_associate_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-015, API-016, API-017 / REQ-003: Search canonical skills, associate with profile, and disassociate."""
    token = tokens["usr_alex_chen"]

    # 1. Search Skills (API-015)
    search_resp = client.get("/api/v1/skills?query=Python", headers=auth_headers(token))
    assert search_resp.status_code == 200
    skills = search_resp.json()
    assert any("python" in s["name"].lower() for s in skills)

    # 2. Associate Skill (API-016)
    unique_skill = f"eBPF Tuning {uuid.uuid4().hex[:4]}"
    add_resp = client.post("/api/v1/users/me/skills", json={"skill_name": unique_skill}, headers=auth_headers(token))
    assert add_resp.status_code == 201, f"Expected 201, got {add_resp.status_code}: {add_resp.text}"
    added_skill = add_resp.json()
    skill_id = added_skill["id"]
    assert added_skill["name"] == unique_skill

    # 3. Disassociate Skill (API-017)
    del_resp = client.delete(f"/api/v1/users/me/skills/{skill_id}", headers=auth_headers(token))
    assert del_resp.status_code == 204


def test_req004_first_degree_badge_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-006 / REQ-004: Direct confirmed connection evaluates to 1st degree badge."""
    # In seeded data, Elena Rostova and Alex Chen have an ACCEPTED connection (conn_01)
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/users/usr_alex_chen", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["id"] == "usr_alex_chen"
    assert data["degree"] == "1st", f"Expected '1st' degree badge, got {data['degree']}"
    assert data["connection_status_with_viewer"] == "ACCEPTED"


def test_req004_second_degree_badge_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-006 / REQ-004: Non-connected user sharing mutual 1st-degree connection evaluates to 2nd badge."""
    # Elena is connected to Alex Chen (conn_01).
    # Alex Chen is connected to Liam Patel (conn_06).
    # Elena is NOT connected to Liam Patel.
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/users/usr_liam_patel", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["id"] == "usr_liam_patel"
    assert data["degree"] == "2nd", f"Expected '2nd' degree badge, got {data['degree']}"
    assert data["mutual_connections_count"] >= 1
    assert len(data["mutual_connections_preview"]) >= 1
    # Check Alex Chen is in the mutual preview
    mutual_ids = [m["id"] for m in data["mutual_connections_preview"]]
    assert "usr_alex_chen" in mutual_ids


def test_req004_mutual_connections_list_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-008 / REQ-004: Explicit mutual connections endpoint lists shared 1st-degree connections."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/users/usr_liam_patel/mutuals", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    mutuals = resp.json()
    assert isinstance(mutuals, list)
    assert len(mutuals) >= 1
    mutual_ids = [m["id"] for m in mutuals]
    assert "usr_alex_chen" in mutual_ids


def test_req004_third_plus_degree_badge_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-006 / REQ-004: Out-of-network user with 0 mutual connections evaluates to 3rd+ degree badge."""
    # In seeded data, Elena shares no mutual connections with Jordan Mendez (usr_jordan_mendez)
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/users/usr_jordan_mendez", headers=auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["degree"] == "3rd+", f"Expected '3rd+' badge, got {data['degree']}"
    assert data["mutual_connections_count"] == 0


def test_req004_self_profile_degree_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-006 / REQ-004: Viewing self profile returns connection_status 'SELF'."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/users/usr_elena_rostova", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["connection_status_with_viewer"] == "SELF"


def test_req004_profile_negative_user_not_found(client: TestClient, tokens: dict, auth_headers):
    """API-006 / REQ-004: Requesting non-existent user profile returns 404 USER_NOT_FOUND."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/users/usr_ghost_not_found_999", headers=auth_headers(token))
    assert resp.status_code == 404
    error = resp.json().get("error", {})
    assert error.get("code") == "USER_NOT_FOUND"

"""Test Suite for Job Board & Mini-ATS Applicant Tracking Pipeline.

Coverage:
- REQ-013: Job Posting Creation (API-036, API-037)
- REQ-014: Job Search and Filtering (API-034, API-035)
- REQ-015: "Easy Apply" Application Submission (API-038, API-041, EDG-003)
- REQ-016: Recruiter Pipeline Candidate Status Management (API-039, API-040)
"""
import uuid
import pytest
from fastapi.testclient import TestClient


def test_req013_create_job_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-036 / REQ-013: Recruiter creates an open job posting with valid salary range and skills."""
    token = tokens["usr_sarah_jenkins"]
    payload = {
        "title": "Principal SRE & Infrastructure Architect",
        "company_name": "Apex Global Cloud",
        "workplace_type": "REMOTE",
        "location": "San Francisco, CA",
        "salary_min": 170000,
        "salary_max": 230000,
        "description": "Architect high-availability Kubernetes platforms, eBPF telemetry, and resilient SQLite WAL storage.",
        "required_skills": ["Kubernetes", "Linux", "eBPF", "Go", "Python"],
    }
    resp = client.post("/api/v1/jobs", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    job = resp.json()
    assert job["id"].startswith("job_")
    assert job["title"] == payload["title"]
    assert job["workplace_type"] == "REMOTE"
    assert job["salary_min"] == 170000
    assert job["salary_max"] == 230000
    assert job["status"] == "OPEN"
    assert "Kubernetes" in job["required_skills"]


def test_req013_create_job_negative_inverted_salary(client: TestClient, tokens: dict, auth_headers):
    """API-036 / REQ-013: Inverted salary range (min > max) returns 422 SALARY_MAX_MUST_EXCEED_MIN."""
    token = tokens["usr_sarah_jenkins"]
    invalid_payload = {
        "title": "Staff Backend Engineer",
        "company_name": "Inverted Pay Corp",
        "workplace_type": "REMOTE",
        "location": "Austin, TX",
        "salary_min": 250000,
        "salary_max": 150000,
        "description": "Faulty job submission with inverted compensation bounds.",
        "required_skills": ["Python"],
    }
    resp = client.post("/api/v1/jobs", json=invalid_payload, headers=auth_headers(token))
    assert resp.status_code == 422
    error = resp.json().get("error", {})
    assert error.get("code") == "SALARY_MAX_MUST_EXCEED_MIN"


def test_req013_toggle_job_status_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-037 / REQ-013: Job poster toggles status from OPEN to CLOSED."""
    token = tokens["usr_sarah_jenkins"]
    # Create job to toggle
    create_resp = client.post(
        "/api/v1/jobs",
        json={
            "title": "Senior Product Designer",
            "company_name": "DesignHub",
            "workplace_type": "HYBRID",
            "location": "Boston, MA",
            "salary_min": 130000,
            "salary_max": 160000,
            "description": "Design design systems and enterprise UX.",
            "required_skills": ["Figma", "Design Systems"],
        },
        headers=auth_headers(token)
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    # Toggle status to CLOSED
    patch_resp = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "CLOSED"},
        headers=auth_headers(token)
    )
    assert patch_resp.status_code == 200, f"Expected 200, got {patch_resp.status_code}: {patch_resp.text}"
    assert patch_resp.json()["status"] == "CLOSED"


def test_req013_toggle_job_status_negative_unauthorized(client: TestClient, tokens: dict, auth_headers):
    """API-037 / REQ-013: Non-poster cannot change job status (403 NOT_JOB_OWNER)."""
    token_priya = tokens["usr_priya_sharma"]
    # job_01 was posted by Sarah Jenkins in seed
    resp = client.patch(
        "/api/v1/jobs/job_01/status",
        json={"status": "CLOSED"},
        headers=auth_headers(token_priya)
    )
    assert resp.status_code == 403
    error = resp.json().get("error", {})
    assert error.get("code") == "NOT_JOB_OWNER"


def test_req014_search_jobs_keyword_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-034 / REQ-014: Filter jobs by keyword in title/description."""
    token = tokens["usr_alex_chen"]
    resp = client.get("/api/v1/jobs?keyword=Engineer", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    assert len(items) >= 1
    for j in items:
        assert "engineer" in j["title"].lower() or "engineer" in j["description"].lower()


def test_req014_search_jobs_workplace_type_filter_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-034 / REQ-014: Filter jobs by workplace type (REMOTE)."""
    token = tokens["usr_alex_chen"]
    resp = client.get("/api/v1/jobs?workplace_type=REMOTE", headers=auth_headers(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    for j in items:
        assert j["workplace_type"] == "REMOTE"


def test_req014_search_jobs_skill_filter_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-034 / REQ-014: Filter jobs by skill tag (Python)."""
    token = tokens["usr_alex_chen"]
    resp = client.get("/api/v1/jobs?skill=Python", headers=auth_headers(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    for j in items:
        assert any("python" in s.lower() for s in j["required_skills"])


def test_req014_get_job_detail_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-035 / REQ-014: Retrieve full job listing details."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/jobs/job_01", headers=auth_headers(token))
    assert resp.status_code == 200
    job = resp.json()
    assert job["id"] == "job_01"
    assert "poster" in job
    assert isinstance(job["required_skills"], list)


def test_req014_get_job_detail_negative_not_found(client: TestClient, tokens: dict, auth_headers):
    """API-035 / REQ-014: Requesting non-existent job returns 404 JOB_NOT_FOUND."""
    token = tokens["usr_elena_rostova"]
    resp = client.get("/api/v1/jobs/job_ghost_999", headers=auth_headers(token))
    assert resp.status_code == 404
    error = resp.json().get("error", {})
    assert error.get("code") == "JOB_NOT_FOUND"


def test_req015_easy_apply_lifecycle_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-038, API-041 / REQ-015: Candidate submits Easy Apply; checks my applications list."""
    token_candidate = tokens["usr_elena_rostova"]
    # Seeded job_02 was posted by Marcus Vance
    apply_payload = {
        "cover_note": "I have 8+ years experience architecting distributed AI pipelines.",
        "resume_url": "/uploads/resumes/resume_elena_rostova.pdf",
    }
    resp = client.post("/api/v1/jobs/job_02/apply", json=apply_payload, headers=auth_headers(token_candidate))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    app = resp.json()
    assert app["job_id"] == "job_02"
    assert app["status"] == "APPLIED"
    assert app["cover_note"] == apply_payload["cover_note"]
    assert app["applicant"]["id"] == "usr_elena_rostova"
    assert isinstance(app["skills_snapshot"], list)

    # Candidate retrieves my applications (API-041)
    my_apps = client.get("/api/v1/jobs/applications/me", headers=auth_headers(token_candidate))
    assert my_apps.status_code == 200
    applied_job_ids = [a["job_id"] for a in my_apps.json()]
    assert "job_02" in applied_job_ids


def test_req015_easy_apply_negative_duplicate_edg003(client: TestClient, tokens: dict, auth_headers):
    """API-038 / REQ-015 / EDG-003: Submitting duplicate application to the same job returns 409 ALREADY_APPLIED_TO_JOB."""
    token_candidate = tokens["usr_elena_rostova"]
    apply_payload = {
        "cover_note": "Duplicate apply attempt.",
        "resume_url": None,
    }
    # Elena already applied to job_02 in previous test
    resp = client.post("/api/v1/jobs/job_02/apply", json=apply_payload, headers=auth_headers(token_candidate))
    assert resp.status_code == 409
    error = resp.json().get("error", {})
    assert error.get("code") == "ALREADY_APPLIED_TO_JOB"


def test_req016_recruiter_pipeline_applications_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-039 / REQ-016: Job poster views applicant pipeline table."""
    token_sarah = tokens["usr_sarah_jenkins"]
    # Sarah posted job_02
    resp = client.get("/api/v1/jobs/job_02/applications", headers=auth_headers(token_sarah))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    apps = resp.json()
    assert isinstance(apps, list)
    assert len(apps) >= 1
    applicant_ids = [a["applicant"]["id"] for a in apps]
    assert "usr_elena_rostova" in applicant_ids


def test_req016_recruiter_pipeline_negative_unauthorized(client: TestClient, tokens: dict, auth_headers):
    """API-039 / REQ-016: Non-job poster attempting to view applicant pipeline returns 403 NOT_JOB_OWNER."""
    token_alex = tokens["usr_alex_chen"]
    # Alex Chen is not the poster of job_02
    resp = client.get("/api/v1/jobs/job_02/applications", headers=auth_headers(token_alex))
    assert resp.status_code == 403
    error = resp.json().get("error", {})
    assert error.get("code") == "NOT_JOB_OWNER"


def test_req016_recruiter_transition_candidate_status_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-040 / REQ-016: Recruiter transitions candidate status from APPLIED to SHORTLISTED."""
    token_sarah = tokens["usr_sarah_jenkins"]
    # Get Elena's application ID on job_02
    apps_resp = client.get("/api/v1/jobs/job_02/applications", headers=auth_headers(token_sarah))
    assert apps_resp.status_code == 200
    elena_app = next(a for a in apps_resp.json() if a["applicant"]["id"] == "usr_elena_rostova")
    app_id = elena_app["id"]

    # Transition to SHORTLISTED
    patch_resp = client.patch(
        f"/api/v1/jobs/job_02/applications/{app_id}/status",
        json={"status": "SHORTLISTED"},
        headers=auth_headers(token_sarah)
    )
    assert patch_resp.status_code == 200, f"Expected 200, got {patch_resp.status_code}: {patch_resp.text}"
    assert patch_resp.json()["status"] == "SHORTLISTED"


def test_req016_recruiter_transition_negative_unauthorized(client: TestClient, tokens: dict, auth_headers):
    """API-040 / REQ-016: Non-owner cannot transition candidate status (403 NOT_JOB_OWNER)."""
    token_priya = tokens["usr_priya_sharma"]
    # Priya is not the owner of job_02
    resp = client.patch(
        "/api/v1/jobs/job_02/applications/app_dummy/status",
        json={"status": "REJECTED"},
        headers=auth_headers(token_priya)
    )
    assert resp.status_code == 403
    error = resp.json().get("error", {})
    assert error.get("code") == "NOT_JOB_OWNER"

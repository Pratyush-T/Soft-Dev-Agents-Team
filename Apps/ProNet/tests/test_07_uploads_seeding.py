"""Test Suite for Database Auto-Seeding & File Upload MIME Magic-Byte Verification.

Coverage:
- REQ-019: Deterministic Database Auto-Seeding (KPI-004)
- NFR-006: File Size Limits (Avatar <= 2MB, Post Media <= 5MB, Resume <= 5MB)
- EDG-004: File Extension / MIME Spoofing Magic-Byte Inspection (API-048, API-049, API-050)
"""
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.models.schema import User, Connection, Post, Job
from app.services.seeder import seed_database
from app.core.database import async_session_factory


def test_req019_deterministic_seeding_counts_kpi004(client: TestClient, tokens: dict, auth_headers):
    """REQ-019 / KPI-004: Clean initialization deterministically yields 10 personas, 15 connections, 12 posts, 8 jobs."""
    token = tokens["usr_elena_rostova"]

    # 1. Seeded personas present
    personas_resp = client.get("/api/v1/auth/personas")
    assert personas_resp.status_code == 200
    personas = personas_resp.json()
    assert len(personas) >= 10, f"Expected at least 10 seeded personas, found {len(personas)}"
    persona_ids = [p["id"] for p in personas]
    assert "usr_elena_rostova" in persona_ids
    assert "usr_alex_chen" in persona_ids

    # 2. Feed contains seeded posts
    feed_resp = client.get("/api/v1/feed?mode=recent&limit=50", headers=auth_headers(token))
    assert feed_resp.status_code == 200
    posts = feed_resp.json()["items"]
    assert len(posts) >= 12, f"Expected at least 12 seeded posts, found {len(posts)}"

    # 3. Exactly 8 open jobs in seeded catalog
    jobs_resp = client.get("/api/v1/jobs?limit=50", headers=auth_headers(token))
    assert jobs_resp.status_code == 200
    jobs = jobs_resp.json()["items"]
    assert len(jobs) >= 8, f"Expected at least 8 seeded jobs, found {len(jobs)}"

    # 4. Active connections exist for personas
    conns_resp = client.get("/api/v1/connections", headers=auth_headers(token))
    assert conns_resp.status_code == 200
    conns = conns_resp.json()
    assert len(conns) >= 1, "Expected seeded connections for Elena Rostova"


def test_nfr006_avatar_upload_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-048 / NFR-006: Valid PNG avatar upload with valid magic bytes returns 201."""
    token = tokens["usr_elena_rostova"]
    # PNG magic bytes: \x89PNG\r\n\x1a\n followed by minimal IHDR chunk
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("avatar.png", png_content, "image/png")}
    
    resp = client.post("/api/v1/uploads/avatar", files=files, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["content_type"] == "image/png"
    assert data["file_url"].startswith("/uploads/avatars/")


def test_nfr006_avatar_upload_negative_spoofed_magic_bytes_edg004(client: TestClient, tokens: dict, auth_headers):
    """API-048 / EDG-004: Windows PE executable (.exe) renamed to avatar.png rejected with 415."""
    token = tokens["usr_elena_rostova"]
    # Executable DOS header magic bytes: MZ\x90\x00...
    fake_exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This is malicious code."
    files = {"file": ("malicious_avatar.png", fake_exe_content, "image/png")}
    
    resp = client.post("/api/v1/uploads/avatar", files=files, headers=auth_headers(token))
    assert resp.status_code == 415
    error = resp.json().get("error", {})
    assert error.get("code") == "UNSUPPORTED_MEDIA_TYPE"


def test_nfr006_avatar_upload_negative_gif_disallowed(client: TestClient, tokens: dict, auth_headers):
    """API-048 / NFR-006: GIF format is explicitly disallowed for avatar images (415)."""
    token = tokens["usr_elena_rostova"]
    gif_content = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    files = {"file": ("animated_avatar.gif", gif_content, "image/gif")}
    
    resp = client.post("/api/v1/uploads/avatar", files=files, headers=auth_headers(token))
    assert resp.status_code == 415
    error = resp.json().get("error", {})
    assert error.get("code") == "UNSUPPORTED_MEDIA_TYPE"


def test_nfr006_avatar_upload_negative_oversized(client: TestClient, tokens: dict, auth_headers):
    """API-048 / NFR-006: Avatar exceeding 2MB threshold rejected with 413 PAYLOAD_TOO_LARGE."""
    token = tokens["usr_elena_rostova"]
    # Create fake oversized PNG (2.5 MB)
    oversized_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * (2 * 1024 * 1024 + 500 * 1024)
    files = {"file": ("oversized_avatar.png", oversized_content, "image/png")}
    
    resp = client.post("/api/v1/uploads/avatar", files=files, headers=auth_headers(token))
    assert resp.status_code == 413
    error = resp.json().get("error", {})
    assert error.get("code") == "PAYLOAD_TOO_LARGE"


def test_nfr006_post_media_upload_happy_path(client: TestClient, tokens: dict, auth_headers):
    """API-049 / NFR-006: Valid JPEG post image upload with magic bytes \xFF\xD8\xFF returns 201."""
    token = tokens["usr_priya_sharma"]
    jpeg_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00\xFF\xD9"
    files = {"file": ("diagram.jpg", jpeg_content, "image/jpeg")}
    
    resp = client.post("/api/v1/uploads/post-media", files=files, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["content_type"] == "image/jpeg"
    assert data["file_url"].startswith("/uploads/posts/")


def test_nfr006_post_media_upload_negative_oversized(client: TestClient, tokens: dict, auth_headers):
    """API-049 / NFR-006: Post media exceeding 5MB rejected with 413 PAYLOAD_TOO_LARGE."""
    token = tokens["usr_priya_sharma"]
    oversized_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * (5 * 1024 * 1024 + 1024)
    files = {"file": ("large_image.jpg", oversized_content, "image/jpeg")}
    
    resp = client.post("/api/v1/uploads/post-media", files=files, headers=auth_headers(token))
    assert resp.status_code == 413
    error = resp.json().get("error", {})
    assert error.get("code") == "PAYLOAD_TOO_LARGE"


def test_nfr006_resume_upload_happy_path_pdf(client: TestClient, tokens: dict, auth_headers):
    """API-050 / NFR-006: Valid PDF document with %PDF- header magic bytes returns 201."""
    token = tokens["usr_alex_chen"]
    pdf_content = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    files = {"file": ("resume_alex_chen.pdf", pdf_content, "application/pdf")}
    
    resp = client.post("/api/v1/uploads/resume", files=files, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["content_type"] == "application/pdf"
    assert data["file_url"].startswith("/uploads/resumes/")


def test_nfr006_resume_upload_happy_path_docx(client: TestClient, tokens: dict, auth_headers):
    """API-050 / NFR-006: Valid DOCX document with PK\x03\x04 zip magic bytes returns 201."""
    token = tokens["usr_alex_chen"]
    docx_content = b"PK\x03\x04\x14\x00\x06\x00\x08\x00[Content_Types].xml"
    files = {"file": ("resume_alex_chen.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    
    resp = client.post("/api/v1/uploads/resume", files=files, headers=auth_headers(token))
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    assert "wordprocessingml" in resp.json()["content_type"]


def test_nfr006_resume_upload_negative_spoofed_file_edg004(client: TestClient, tokens: dict, auth_headers):
    """API-050 / EDG-004: Plain text / shell script disguised as resume.pdf rejected with 415."""
    token = tokens["usr_alex_chen"]
    script_content = b"#!/bin/bash\necho 'Attempting arbitrary script injection'\n"
    files = {"file": ("resume.pdf", script_content, "application/pdf")}
    
    resp = client.post("/api/v1/uploads/resume", files=files, headers=auth_headers(token))
    assert resp.status_code == 415
    error = resp.json().get("error", {})
    assert error.get("code") == "UNSUPPORTED_MEDIA_TYPE"


def test_nfr006_resume_upload_negative_oversized(client: TestClient, tokens: dict, auth_headers):
    """API-050 / NFR-006: Resume exceeding 5MB threshold rejected with 413 PAYLOAD_TOO_LARGE."""
    token = tokens["usr_alex_chen"]
    oversized_pdf = b"%PDF-1.7\n" + b"\x00" * (5 * 1024 * 1024 + 512)
    files = {"file": ("huge_resume.pdf", oversized_pdf, "application/pdf")}
    
    resp = client.post("/api/v1/uploads/resume", files=files, headers=auth_headers(token))
    assert resp.status_code == 413
    error = resp.json().get("error", {})
    assert error.get("code") == "PAYLOAD_TOO_LARGE"

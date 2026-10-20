"""Local filesystem file and media upload API router with magic-byte verification (API-048 through API-050)."""
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, status

from app.core.config import settings
from app.core.exceptions import (
    PayloadTooLargeException,
    UnsupportedMediaTypeException,
)
from app.api.deps import get_current_user
from app.models.schema import User
from app.schemas.contracts import UploadResponseDTO

router = APIRouter(prefix="/uploads", tags=["File & Media Uploads"])


def verify_image_magic_bytes(header: bytes) -> str:
    """Validate image magic bytes against supported signatures."""
    if len(header) < 12:
        raise UnsupportedMediaTypeException()
    if header.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return "image/gif"
    raise UnsupportedMediaTypeException()


def verify_doc_magic_bytes(header: bytes) -> str:
    """Validate PDF or DOCX magic bytes."""
    if len(header) < 4:
        raise UnsupportedMediaTypeException()
    if header.startswith(b"%PDF-"):
        return "application/pdf"
    elif header.startswith(b"PK\x03\x04"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    raise UnsupportedMediaTypeException()


@router.post("/avatar", response_model=UploadResponseDTO, status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """API-048: Upload user profile avatar photo (max 2MB, JPEG/PNG/WEBP)."""
    contents = await file.read()
    size = len(contents)
    if size > settings.PRONET_MAX_AVATAR_BYTES:
        raise PayloadTooLargeException(f"Avatar file size ({size} bytes) exceeds 2MB limit.")

    mime_type = verify_image_magic_bytes(contents[:2048])
    if mime_type == "image/gif":
        raise UnsupportedMediaTypeException("GIF avatars are not supported.")

    ext = ".jpg" if mime_type == "image/jpeg" else (".png" if mime_type == "image/png" else ".webp")
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"

    upload_dir = Path(settings.PRONET_UPLOAD_DIR) / "avatars"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / filename

    with open(target_path, "wb") as f:
        f.write(contents)

    file_url = f"/uploads/avatars/{filename}"
    return UploadResponseDTO(
        file_url=file_url,
        file_name=filename,
        content_type=mime_type,
        size_bytes=size,
    )


@router.post("/post-media", response_model=UploadResponseDTO, status_code=status.HTTP_201_CREATED)
async def upload_post_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """API-049: Upload post attached image (max 5MB, JPEG/PNG/WEBP/GIF)."""
    contents = await file.read()
    size = len(contents)
    if size > settings.PRONET_MAX_POST_MEDIA_BYTES:
        raise PayloadTooLargeException(f"Post media file size ({size} bytes) exceeds 5MB limit.")

    mime_type = verify_image_magic_bytes(contents[:2048])
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif"
    }
    ext = ext_map.get(mime_type, ".jpg")
    filename = f"post_{uuid.uuid4().hex[:12]}{ext}"

    upload_dir = Path(settings.PRONET_UPLOAD_DIR) / "posts"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / filename

    with open(target_path, "wb") as f:
        f.write(contents)

    file_url = f"/uploads/posts/{filename}"
    return UploadResponseDTO(
        file_url=file_url,
        file_name=filename,
        content_type=mime_type,
        size_bytes=size,
    )


@router.post("/resume", response_model=UploadResponseDTO, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """API-050: Upload candidate job application resume (max 5MB, PDF/DOCX)."""
    contents = await file.read()
    size = len(contents)
    if size > settings.PRONET_MAX_RESUME_BYTES:
        raise PayloadTooLargeException(f"Resume file size ({size} bytes) exceeds 5MB limit.")

    mime_type = verify_doc_magic_bytes(contents[:2048])
    ext = ".pdf" if mime_type == "application/pdf" else ".docx"
    filename = f"resume_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"

    upload_dir = Path(settings.PRONET_UPLOAD_DIR) / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / filename

    with open(target_path, "wb") as f:
        f.write(contents)

    file_url = f"/uploads/resumes/{filename}"
    return UploadResponseDTO(
        file_url=file_url,
        file_name=filename,
        content_type=mime_type,
        size_bytes=size,
    )

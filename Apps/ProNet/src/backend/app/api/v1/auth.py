"""Authentication and Persona Switcher API Router (API-001 through API-005)."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
    ConnectionAlreadyRequestedException,
)
from app.api.deps import get_current_user
from app.models.schema import User, Profile
from app.schemas.contracts import (
    RegisterRequestDTO,
    LoginRequestDTO,
    QuickSwitchRequestDTO,
    AuthTokensDTO,
    UserSummaryDTO,
    PersonaDTO,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Persona"])


@router.post("/register", response_model=AuthTokensDTO, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterRequestDTO,
    db: AsyncSession = Depends(get_db),
):
    """API-001: Register a new user account with bcrypt password hashing."""
    stmt = select(User).where(User.email == body.email)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise ConnectionAlreadyRequestedException(
            message="An account with this email address already exists.",
            details={"email": body.email}
        )

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        is_active=True,
    )
    db.add(user)

    profile = Profile(
        id=f"prf_{user_id}",
        user_id=user_id,
        headline=body.headline,
        location=body.location,
        connections_count=0,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return AuthTokensDTO(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=86400,
        user=UserSummaryDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            headline=profile.headline,
            avatar_url=profile.avatar_url,
        )
    )


@router.post("/login", response_model=AuthTokensDTO, status_code=status.HTTP_200_OK)
async def login_user(
    body: LoginRequestDTO,
    db: AsyncSession = Depends(get_db),
):
    """API-002: Authenticate user credentials and return bearer access token."""
    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.email == body.email)
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise InvalidCredentialsException()

    token = create_access_token(subject=user.id)
    profile = user.profile
    return AuthTokensDTO(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=86400,
        user=UserSummaryDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            headline=profile.headline if profile else "",
            avatar_url=profile.avatar_url if profile else None,
        )
    )


@router.post("/quick-switch", response_model=AuthTokensDTO, status_code=status.HTTP_200_OK)
async def quick_switch_persona(
    body: QuickSwitchRequestDTO,
    db: AsyncSession = Depends(get_db),
):
    """API-003: Instantly switch active persona without credentials (development / evaluation)."""
    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == body.user_id, User.is_active == True)
    )
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise UserNotFoundException(f"Persona '{body.user_id}' does not exist.")

    token = create_access_token(subject=user.id)
    profile = user.profile
    return AuthTokensDTO(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=86400,
        user=UserSummaryDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            headline=profile.headline if profile else "",
            avatar_url=profile.avatar_url if profile else None,
        )
    )


@router.get("/personas", response_model=List[PersonaDTO], status_code=status.HTTP_200_OK)
async def list_personas(
    db: AsyncSession = Depends(get_db),
):
    """API-004: List all seeded user personas for persona switcher UI."""
    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.is_active == True)
        .order_by(User.id.asc())
    )
    res = await db.execute(stmt)
    users = res.scalars().all()

    personas: List[PersonaDTO] = []
    for u in users:
        p = u.profile
        personas.append(
            PersonaDTO(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                headline=p.headline if p else "",
                location=p.location if p else "",
                avatar_url=p.avatar_url if p else None,
            )
        )
    return personas


@router.get("/me", response_model=UserSummaryDTO, status_code=status.HTTP_200_OK)
async def get_current_user_summary(
    current_user: User = Depends(get_current_user),
):
    """API-005: Retrieve currently authenticated user summary."""
    profile = current_user.profile
    return UserSummaryDTO(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        headline=profile.headline if profile else "",
        avatar_url=profile.avatar_url if profile else None,
    )

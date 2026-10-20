"""FastAPI dependencies for authentication, database session, and current user context."""
from typing import Optional
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, UserNotFoundException
from app.models.schema import User, Profile

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Retrieve authenticated user if bearer token is present and valid; else None."""
    if not auth_header or not auth_header.credentials:
        return None
    try:
        payload = decode_access_token(auth_header.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id, User.is_active == True)
        )
        result = await db.execute(stmt)
        return result.scalars().first()
    except Exception:
        return None


async def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Retrieve authenticated user; raises UnauthorizedException if token is missing or invalid."""
    if not auth_header or not auth_header.credentials:
        raise UnauthorizedException("Authentication token is required.")

    payload = decode_access_token(auth_header.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Malformed token claims.")

    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == user_id, User.is_active == True)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise UserNotFoundException("User associated with this token was not found.")
    return user

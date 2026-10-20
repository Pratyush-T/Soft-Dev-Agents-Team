"""Dedicated Feed Router (API-025)."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.schema import User
from app.schemas.contracts import FeedResponseDTO
from app.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["Activity Feed"])


@router.get("", response_model=FeedResponseDTO, status_code=status.HTTP_200_OK)
async def get_activity_feed(
    mode: str = Query("top", pattern="^(recent|top)$"),
    limit: int = Query(20, ge=1, le=50),
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-025: Retrieve paginated dual-mode activity feed."""
    return await FeedService.get_feed(
        viewer_id=current_user.id,
        mode=mode,
        limit=limit,
        cursor=cursor,
        db=db,
    )

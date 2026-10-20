"""Notifications and live badge counter API router (API-045 through API-047)."""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.schema import Notification, User, Profile
from app.schemas.contracts import (
    NotificationDTO,
    BadgeCountsDTO,
    MarkNotificationsReadRequestDTO,
    MarkNotificationsReadResponseDTO,
    UserSummaryDTO,
    NotificationType,
    ReferenceType,
    CursorPaginatedResponse,
)
from app.api.ws.manager import manager

logger = logging.getLogger("pronet.notifications")
router = APIRouter(prefix="/notifications", tags=["Notifications & Badges"])


def format_user_summary(user: User) -> UserSummaryDTO:
    """Build UserSummaryDTO from User and Profile."""
    p = user.profile
    return UserSummaryDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        headline=p.headline if p else "",
        avatar_url=p.avatar_url if p else None,
    )


@router.get("", response_model=CursorPaginatedResponse[NotificationDTO], status_code=status.HTTP_200_OK)
async def list_notifications(
    limit: int = Query(20, ge=1, le=50),
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-045: List user notifications with cursor pagination."""
    stmt = (
        select(Notification)
        .options(selectinload(Notification.actor).selectinload(User.profile))
        .where(Notification.user_id == current_user.id)
    )

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            stmt = stmt.where(Notification.created_at < cursor_dt)
        except Exception as exc:
            logger.debug("Failed parsing cursor datetime for notifications query: %s (%s)", cursor, exc)

    fetch_limit = min(limit, 50) + 1
    stmt = stmt.order_by(Notification.created_at.desc()).limit(fetch_limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()

    has_more = len(rows) > min(limit, 50)
    target_notifs = rows[:min(limit, 50)]

    items = [
        NotificationDTO(
            id=n.id,
            user_id=n.user_id,
            actor=format_user_summary(n.actor),
            notification_type=NotificationType(n.notification_type),
            title=n.title,
            content=n.content,
            reference_id=n.reference_id,
            reference_type=ReferenceType(n.reference_type) if n.reference_type else None,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in target_notifs
    ]

    next_cursor = None
    if has_more and target_notifs:
        c_val = target_notifs[-1].created_at
        if hasattr(c_val, "isoformat"):
            next_cursor = c_val.isoformat().replace("+00:00", "Z")

    return CursorPaginatedResponse[NotificationDTO](
        items=items,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.post("/read", response_model=MarkNotificationsReadResponseDTO, status_code=status.HTTP_200_OK)
async def mark_notifications_read(
    body: Optional[MarkNotificationsReadRequestDTO] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-046: Mark specific or all notifications as read."""
    stmt = update(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    if body and body.notification_ids:
        stmt = stmt.where(Notification.id.in_(body.notification_ids))

    stmt = stmt.values(is_read=True)
    res = await db.execute(stmt)
    await db.commit()
    marked_count = res.rowcount or 0

    await manager.push_badge_update(current_user.id, db)
    return MarkNotificationsReadResponseDTO(success=True, marked_count=marked_count)


@router.get("/badges", response_model=BadgeCountsDTO, status_code=status.HTTP_200_OK)
async def get_badge_counts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-047: Get unread badge counts (messages, connections, alerts)."""
    counts = await manager.calculate_badges(current_user.id, db)
    return BadgeCountsDTO(**counts)

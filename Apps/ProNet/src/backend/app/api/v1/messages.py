"""Direct messaging API router (API-042 through API-044)."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import (
    MustBeFirstDegreeException,
    UserNotFoundException,
)
from app.api.deps import get_current_user
from app.models.schema import Message, User, Profile
from app.schemas.contracts import (
    MessageDTO,
    ConversationSummaryDTO,
    UserSummaryDTO,
    MarkConversationReadResponseDTO,
    CursorPaginatedResponse,
)
from app.services.graph_service import GraphService
from app.api.ws.manager import manager

logger = logging.getLogger("pronet.messages")
router = APIRouter(prefix="/messages", tags=["Direct Messaging"])


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


@router.get("/conversations", response_model=List[ConversationSummaryDTO], status_code=status.HTTP_200_OK)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-042: List conversation summaries with most recent messages and unread counts."""
    # Find all messages involving current_user
    stmt = (
        select(Message)
        .where(or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id))
        .order_by(Message.created_at.desc())
    )
    res = await db.execute(stmt)
    all_msgs = res.scalars().all()

    # Group by peer ID
    peers_last_msg: Dict[str, Message] = {}
    peers_unread_cnt: Dict[str, int] = {}

    for m in all_msgs:
        peer_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
        if peer_id not in peers_last_msg:
            peers_last_msg[peer_id] = m
            peers_unread_cnt[peer_id] = 0

        if m.recipient_id == current_user.id and m.read_at is None:
            peers_unread_cnt[peer_id] += 1

    if not peers_last_msg:
        return []

    # Hydrate peer users
    peer_ids = list(peers_last_msg.keys())
    users_stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.id.in_(peer_ids))
    )
    users_res = await db.execute(users_stmt)
    user_map = {u.id: u for u in users_res.scalars().all()}

    conversations: List[ConversationSummaryDTO] = []
    for pid, l_msg in peers_last_msg.items():
        if pid not in user_map:
            continue
        peer_user = user_map[pid]
        conversations.append(
            ConversationSummaryDTO(
                peer=format_user_summary(peer_user),
                last_message=MessageDTO(
                    id=l_msg.id,
                    sender_id=l_msg.sender_id,
                    recipient_id=l_msg.recipient_id,
                    content=l_msg.content,
                    read_at=l_msg.read_at,
                    created_at=l_msg.created_at,
                    is_outgoing=(l_msg.sender_id == current_user.id),
                ),
                unread_count=peers_unread_cnt.get(pid, 0),
            )
        )

    return conversations


@router.get("/{peer_id}", response_model=CursorPaginatedResponse[MessageDTO], status_code=status.HTTP_200_OK)
async def get_message_history(
    peer_id: str,
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-043: Get conversation history with confirmed 1st-degree connection."""
    # Enforce 1st-degree guard
    is_friend = await GraphService.is_first_degree(current_user.id, peer_id, db)
    if not is_friend:
        raise MustBeFirstDegreeException()

    stmt = select(Message).where(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == peer_id),
            and_(Message.sender_id == peer_id, Message.recipient_id == current_user.id),
        )
    )

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            stmt = stmt.where(Message.created_at < cursor_dt)
        except Exception as exc:
            logger.debug("Failed parsing cursor datetime for messages query: %s (%s)", cursor, exc)

    fetch_limit = min(limit, 100) + 1
    stmt = stmt.order_by(Message.created_at.desc()).limit(fetch_limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()

    has_more = len(rows) > min(limit, 100)
    target_msgs = rows[:min(limit, 100)]

    # Reverse to return chronological order for chat view
    target_msgs.reverse()

    items = [
        MessageDTO(
            id=m.id,
            sender_id=m.sender_id,
            recipient_id=m.recipient_id,
            content=m.content,
            read_at=m.read_at,
            created_at=m.created_at,
            is_outgoing=(m.sender_id == current_user.id),
        )
        for m in target_msgs
    ]

    next_cursor = None
    if has_more and target_msgs:
        c_val = target_msgs[0].created_at
        if hasattr(c_val, "isoformat"):
            next_cursor = c_val.isoformat().replace("+00:00", "Z")

    return CursorPaginatedResponse[MessageDTO](
        items=items,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.post("/{peer_id}/read", response_model=MarkConversationReadResponseDTO, status_code=status.HTTP_200_OK)
async def mark_conversation_read(
    peer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-044: Mark all unread incoming messages from peer as read."""
    now_utc = datetime.now(timezone.utc)
    stmt = (
        update(Message)
        .where(
            Message.sender_id == peer_id,
            Message.recipient_id == current_user.id,
            Message.read_at.is_(None)
        )
        .values(read_at=now_utc)
    )
    result = await db.execute(stmt)
    await db.commit()
    marked_count = result.rowcount or 0

    await manager.push_badge_update(current_user.id, db)
    return MarkConversationReadResponseDTO(marked_count=marked_count)

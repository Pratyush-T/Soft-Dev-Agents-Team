"""Social graph connections API router (API-018 through API-024)."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, update, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import (
    SelfConnectionForbiddenException,
    ConnectionAlreadyRequestedException,
    AlreadyConnectedException,
    CannotWithdrawAcceptedConnectionException,
    ResourceNotFoundException,
    UserNotFoundException,
)
from app.api.deps import get_current_user
from app.models.schema import Connection, User, Profile, Notification
from app.schemas.contracts import (
    ConnectionDTO,
    PendingConnectionsDTO,
    SendConnectionRequestDTO,
    UserSummaryDTO,
    ConnectionStatus,
)
from app.api.ws.manager import manager

router = APIRouter(prefix="/connections", tags=["Social Graph & Connections"])


def build_connection_dto(conn: Connection, viewer_id: str) -> ConnectionDTO:
    """Format Connection ORM model into API contract DTO with peer summary."""
    peer = conn.user_high if conn.user_low_id == viewer_id else conn.user_low
    profile = peer.profile if peer else None
    peer_summary = UserSummaryDTO(
        id=peer.id if peer else "",
        email=peer.email if peer else "",
        full_name=peer.full_name if peer else "",
        headline=profile.headline if profile else "",
        avatar_url=profile.avatar_url if profile else None,
    )
    return ConnectionDTO(
        id=conn.id,
        user_low_id=conn.user_low_id,
        user_high_id=conn.user_high_id,
        initiator_id=conn.initiator_id,
        recipient_id=conn.recipient_id,
        status=ConnectionStatus(conn.status),
        note=conn.note,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
        peer=peer_summary,
    )


@router.get("", response_model=List[ConnectionDTO], status_code=status.HTTP_200_OK)
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-018: List confirmed 1st-degree connections for the authenticated user."""
    stmt = (
        select(Connection)
        .options(
            selectinload(Connection.user_low).selectinload(User.profile),
            selectinload(Connection.user_high).selectinload(User.profile),
        )
        .where(
            or_(Connection.user_low_id == current_user.id, Connection.user_high_id == current_user.id),
            Connection.status == "ACCEPTED"
        )
        .order_by(Connection.updated_at.desc())
    )
    res = await db.execute(stmt)
    conns = res.scalars().all()
    return [build_connection_dto(c, current_user.id) for c in conns]


@router.get("/pending", response_model=PendingConnectionsDTO, status_code=status.HTTP_200_OK)
async def list_pending_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-019: List incoming and outgoing pending connection requests."""
    # Incoming
    inc_stmt = (
        select(Connection)
        .options(
            selectinload(Connection.user_low).selectinload(User.profile),
            selectinload(Connection.user_high).selectinload(User.profile),
        )
        .where(
            Connection.recipient_id == current_user.id,
            Connection.status == "PENDING"
        )
        .order_by(Connection.created_at.desc())
    )
    inc_res = await db.execute(inc_stmt)
    incoming = [build_connection_dto(c, current_user.id) for c in inc_res.scalars().all()]

    # Outgoing
    out_stmt = (
        select(Connection)
        .options(
            selectinload(Connection.user_low).selectinload(User.profile),
            selectinload(Connection.user_high).selectinload(User.profile),
        )
        .where(
            Connection.initiator_id == current_user.id,
            Connection.status == "PENDING"
        )
        .order_by(Connection.created_at.desc())
    )
    out_res = await db.execute(out_stmt)
    outgoing = [build_connection_dto(c, current_user.id) for c in out_res.scalars().all()]

    return PendingConnectionsDTO(incoming=incoming, outgoing=outgoing)


@router.post("/request", response_model=ConnectionDTO, status_code=status.HTTP_201_CREATED)
async def send_connection_request(
    body: SendConnectionRequestDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-020: Send connection request with auto-resolve collision interception (EDG-001)."""
    recipient_id = body.recipient_id
    if current_user.id == recipient_id:
        raise SelfConnectionForbiddenException()

    # Verify recipient exists
    recip = await db.get(User, recipient_id)
    if not recip:
        raise UserNotFoundException(f"Target recipient '{recipient_id}' not found.")

    u_low = min(current_user.id, recipient_id)
    u_high = max(current_user.id, recipient_id)

    stmt = (
        select(Connection)
        .options(
            selectinload(Connection.user_low).selectinload(User.profile),
            selectinload(Connection.user_high).selectinload(User.profile),
        )
        .where(Connection.user_low_id == u_low, Connection.user_high_id == u_high)
    )
    res = await db.execute(stmt)
    edge = res.scalars().first()

    if edge:
        if edge.status == "ACCEPTED":
            raise AlreadyConnectedException()
        elif edge.status == "PENDING":
            if edge.initiator_id == current_user.id:
                raise ConnectionAlreadyRequestedException()
            else:
                # Reciprocal Collision (EDG-001): Auto-Resolve to ACCEPTED
                edge.status = "ACCEPTED"
                # Update connections count on both profiles
                await db.execute(
                    update(Profile)
                    .where(Profile.user_id.in_([current_user.id, recipient_id]))
                    .values(connections_count=Profile.connections_count + 1)
                )
                # Dispatch notification
                notif = Notification(
                    id=f"notif_{uuid.uuid4().hex[:12]}",
                    user_id=recipient_id,
                    actor_id=current_user.id,
                    notification_type="CONNECTION_ACCEPTED",
                    title="Connection Accepted",
                    content=f"You and {current_user.full_name} are now connected.",
                    reference_id=edge.id,
                    reference_type="CONNECTION",
                    is_read=False,
                )
                db.add(notif)
                await db.commit()
                await db.refresh(edge)

                await manager.push_badge_update(recipient_id, db)
                await manager.push_badge_update(current_user.id, db)
                return build_connection_dto(edge, current_user.id)
        elif edge.status == "IGNORED":
            # Reset to pending with current user as initiator
            edge.status = "PENDING"
            edge.initiator_id = current_user.id
            edge.recipient_id = recipient_id
            edge.note = body.note
            await db.commit()
            await db.refresh(edge)
            await manager.push_badge_update(recipient_id, db)
            return build_connection_dto(edge, current_user.id)

    # Create new connection request
    conn_id = f"conn_{uuid.uuid4().hex[:12]}"
    new_edge = Connection(
        id=conn_id,
        user_low_id=u_low,
        user_high_id=u_high,
        initiator_id=current_user.id,
        recipient_id=recipient_id,
        status="PENDING",
        note=body.note,
    )
    db.add(new_edge)

    notif = Notification(
        id=f"notif_{uuid.uuid4().hex[:12]}",
        user_id=recipient_id,
        actor_id=current_user.id,
        notification_type="CONNECTION_REQUEST",
        title="Connection Request",
        content=f"{current_user.full_name} sent you a connection request.",
        reference_id=conn_id,
        reference_type="CONNECTION",
        is_read=False,
    )
    db.add(notif)
    await db.commit()

    # Re-fetch with loaded profiles
    refreshed = await db.execute(
        select(Connection)
        .options(
            selectinload(Connection.user_low).selectinload(User.profile),
            selectinload(Connection.user_high).selectinload(User.profile),
        )
        .where(Connection.id == conn_id)
    )
    conn_result = refreshed.scalars().first()
    await manager.push_badge_update(recipient_id, db)
    return build_connection_dto(conn_result, current_user.id)


@router.post("/{connection_id}/accept", response_model=ConnectionDTO, status_code=status.HTTP_200_OK)
async def accept_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-021: Accept incoming pending connection request."""
    stmt = (
        select(Connection)
        .options(
            selectinload(Connection.user_low).selectinload(User.profile),
            selectinload(Connection.user_high).selectinload(User.profile),
        )
        .where(Connection.id == connection_id)
    )
    res = await db.execute(stmt)
    conn = res.scalars().first()
    if not conn or conn.recipient_id != current_user.id:
        raise ResourceNotFoundException("Pending connection request not found.")

    conn.status = "ACCEPTED"
    # Increment connections count on both profiles
    await db.execute(
        update(Profile)
        .where(Profile.user_id.in_([conn.user_low_id, conn.user_high_id]))
        .values(connections_count=Profile.connections_count + 1)
    )

    notif = Notification(
        id=f"notif_{uuid.uuid4().hex[:12]}",
        user_id=conn.initiator_id,
        actor_id=current_user.id,
        notification_type="CONNECTION_ACCEPTED",
        title="Connection Accepted",
        content=f"{current_user.full_name} accepted your connection request.",
        reference_id=conn.id,
        reference_type="CONNECTION",
        is_read=False,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(conn)

    await manager.push_badge_update(conn.initiator_id, db)
    await manager.push_badge_update(current_user.id, db)
    return build_connection_dto(conn, current_user.id)


@router.post("/{connection_id}/ignore", response_model=ConnectionDTO, status_code=status.HTTP_200_OK)
async def ignore_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-022: Ignore incoming pending connection request."""
    stmt = (
        select(Connection)
        .options(
            selectinload(Connection.user_low).selectinload(User.profile),
            selectinload(Connection.user_high).selectinload(User.profile),
        )
        .where(Connection.id == connection_id)
    )
    res = await db.execute(stmt)
    conn = res.scalars().first()
    if not conn or conn.recipient_id != current_user.id:
        raise ResourceNotFoundException("Pending connection request not found.")

    conn.status = "IGNORED"
    await db.commit()
    await db.refresh(conn)
    await manager.push_badge_update(current_user.id, db)
    return build_connection_dto(conn, current_user.id)


@router.delete("/{connection_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-023: Withdraw outgoing pending connection request."""
    stmt = select(Connection).where(Connection.id == connection_id)
    res = await db.execute(stmt)
    conn = res.scalars().first()
    if not conn or conn.initiator_id != current_user.id:
        raise ResourceNotFoundException("Connection request not found.")

    if conn.status == "ACCEPTED":
        raise CannotWithdrawAcceptedConnectionException()

    recipient_id = conn.recipient_id
    await db.delete(conn)
    await db.commit()

    await manager.push_badge_update(recipient_id, db)
    await manager.push_badge_update(current_user.id, db)
    return None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_connection(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-024: Remove / disconnect confirmed 1st-degree connection."""
    u_low = min(current_user.id, user_id)
    u_high = max(current_user.id, user_id)

    stmt = select(Connection).where(
        Connection.user_low_id == u_low,
        Connection.user_high_id == u_high
    )
    res = await db.execute(stmt)
    conn = res.scalars().first()
    if not conn:
        raise ResourceNotFoundException("Connection not found.")

    was_accepted = (conn.status == "ACCEPTED")
    await db.delete(conn)

    if was_accepted:
        await db.execute(
            update(Profile)
            .where(Profile.user_id.in_([current_user.id, user_id]))
            .values(connections_count=func.max(0, Profile.connections_count - 1))
        )

    await db.commit()
    await manager.push_badge_update(user_id, db)
    await manager.push_badge_update(current_user.id, db)
    return None

"""WebSocket route handler implementing full-duplex messaging, presence, and alerts."""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.core.security import decode_access_token
from app.models.schema import User, Connection, Message, Notification
from app.api.ws.manager import manager

logger = logging.getLogger("pronet.websocket")
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """Authenticated full-duplex WebSocket endpoint."""
    if not token:
        await websocket.close(code=4001, reason="Unauthorized: Missing Token")
        return

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Unauthorized: Missing Subject")
            return
    except Exception as e:
        logger.warning(f"WebSocket token validation failed: {e}")
        await websocket.close(code=4001, reason="Unauthorized: Invalid Token")
        return

    # Verify user exists and is active
    async with async_session_factory() as db:
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id, User.is_active == True)
        )
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            await websocket.close(code=4001, reason="Unauthorized: User Not Found")
            return

        # Register connection
        await manager.connect(user.id, websocket)

        # Initial connect welcome frame
        online_connections = await manager.get_online_connections(user.id, db)
        badges = await manager.calculate_badges(user.id, db)
        session_id = f"sess_{uuid.uuid4().hex[:8]}"

        welcome_frame = {
            "type": "CONNECTED",
            "user_id": user.id,
            "session_id": session_id,
            "online_connection_ids": online_connections,
            "badges": badges,
        }
        await websocket.send_text(json.dumps(welcome_frame))

        # Broadcast presence to online friends
        await manager.broadcast_presence(user.id, True, db)

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except Exception:
                await websocket.send_text(json.dumps({
                    "type": "ERROR",
                    "code": "INVALID_FRAME",
                    "message": "Malformed JSON frame received."
                }))
                continue

            msg_type = data.get("type", "").upper()

            # Heartbeat Ping
            if msg_type == "PING":
                await websocket.send_text(json.dumps({
                    "type": "PONG",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }))
                continue

            # Real-time message transmission
            elif msg_type == "SEND_MESSAGE":
                client_msg_id = data.get("client_msg_id", f"tmp_{uuid.uuid4().hex[:6]}")
                recipient_id = data.get("recipient_id")
                content = (data.get("content") or "").strip()

                if not recipient_id or not content:
                    await websocket.send_text(json.dumps({
                        "type": "ERROR",
                        "code": "INVALID_PAYLOAD",
                        "message": "Recipient ID and message content are required."
                    }))
                    continue

                async with async_session_factory() as db:
                    # 1st-degree connection guard
                    u_low = min(user.id, recipient_id)
                    u_high = max(user.id, recipient_id)
                    conn_stmt = select(Connection).where(
                        Connection.user_low_id == u_low,
                        Connection.user_high_id == u_high,
                        Connection.status == "ACCEPTED"
                    )
                    conn_res = await db.execute(conn_stmt)
                    conn = conn_res.scalars().first()

                    if not conn:
                        await websocket.send_text(json.dumps({
                            "type": "ERROR",
                            "code": "MUST_BE_FIRST_DEGREE_CONNECTION",
                            "message": "Cannot transmit direct message. Recipient is not a confirmed 1st-degree connection.",
                            "details": {"target_user_id": recipient_id}
                        }))
                        continue

                    # Persist message
                    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
                    now_utc = datetime.now(timezone.utc)
                    new_msg = Message(
                        id=msg_id,
                        sender_id=user.id,
                        recipient_id=recipient_id,
                        content=content,
                        created_at=now_utc
                    )
                    db.add(new_msg)
                    await db.commit()

                    is_recipient_online = manager.is_user_online(recipient_id)
                    formatted_time = now_utc.isoformat().replace("+00:00", "Z")

                    if is_recipient_online:
                        # Deliver live to recipient
                        headline = user.profile.headline if user.profile else ""
                        avatar_url = user.profile.avatar_url if user.profile else None
                        await manager.send_personal_message(recipient_id, {
                            "type": "NEW_MESSAGE",
                            "message": {
                                "id": msg_id,
                                "sender_id": user.id,
                                "recipient_id": recipient_id,
                                "content": content,
                                "created_at": formatted_time,
                                "sender_summary": {
                                    "id": user.id,
                                    "full_name": user.full_name,
                                    "headline": headline,
                                    "avatar_url": avatar_url,
                                }
                            }
                        })
                        # Acknowledge to sender
                        await websocket.send_text(json.dumps({
                            "type": "MESSAGE_ACK",
                            "client_msg_id": client_msg_id,
                            "message_id": msg_id,
                            "recipient_id": recipient_id,
                            "status": "DELIVERED",
                            "created_at": formatted_time
                        }))
                        # Push live badge updates
                        await manager.push_badge_update(recipient_id, db)
                    else:
                        # Persist offline notification
                        notif_id = f"notif_{uuid.uuid4().hex[:12]}"
                        notif = Notification(
                            id=notif_id,
                            user_id=recipient_id,
                            actor_id=user.id,
                            notification_type="NEW_MESSAGE",
                            title="New Message",
                            content=f"{user.full_name} sent you a message.",
                            reference_id=msg_id,
                            reference_type="MESSAGE",
                            is_read=False,
                            created_at=now_utc
                        )
                        db.add(notif)
                        await db.commit()

                        # Acknowledge to sender with SENT_OFFLINE
                        await websocket.send_text(json.dumps({
                            "type": "MESSAGE_ACK",
                            "client_msg_id": client_msg_id,
                            "message_id": msg_id,
                            "recipient_id": recipient_id,
                            "status": "SENT_OFFLINE",
                            "created_at": formatted_time
                        }))

            # Typing status relay
            elif msg_type == "TYPING":
                recipient_id = data.get("recipient_id")
                is_typing = bool(data.get("is_typing", False))
                if recipient_id and manager.is_user_online(recipient_id):
                    await manager.send_personal_message(recipient_id, {
                        "type": "PEER_TYPING",
                        "user_id": user.id,
                        "is_typing": is_typing,
                    })

            # Read acknowledgment
            elif msg_type == "READ_ACK":
                peer_id = data.get("conversation_peer_id")
                if peer_id:
                    async with async_session_factory() as db:
                        now_utc = datetime.now(timezone.utc)
                        stmt = (
                            update(Message)
                            .where(
                                Message.sender_id == peer_id,
                                Message.recipient_id == user.id,
                                Message.read_at.is_(None)
                            )
                            .values(read_at=now_utc)
                        )
                        await db.execute(stmt)
                        await db.commit()
                        await manager.push_badge_update(user.id, db)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"WebSocket runtime error for user {user.id}: {e}")
    finally:
        user_went_offline = manager.disconnect(user.id, websocket)
        if user_went_offline:
            async with async_session_factory() as db:
                await manager.broadcast_presence(user.id, False, db)

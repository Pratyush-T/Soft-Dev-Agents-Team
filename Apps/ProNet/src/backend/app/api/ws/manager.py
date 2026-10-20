"""WebSocket ConnectionManager for in-memory multi-user routing, presence, and live pushes."""
import json
import logging
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.schema import Message, Notification, Connection

logger = logging.getLogger("pronet.websocket")


class ConnectionManager:
    """Thread-safe in-process WebSocket connection and dispatch manager."""
    def __init__(self):
        # Maps user_id -> Set of active WebSocket instances (supporting multiple browser tabs)
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Register newly connected WebSocket client."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Active sockets for user: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: str, websocket: WebSocket) -> bool:
        """Remove WebSocket connection. Returns True if user has no remaining active sockets."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                logger.info(f"User {user_id} completely disconnected.")
                return True
        return False

    def is_user_online(self, user_id: str) -> bool:
        """Check if user has at least one active WebSocket connection."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    def get_online_users(self) -> Set[str]:
        """Return set of all currently connected user IDs."""
        return set(self.active_connections.keys())

    async def send_personal_message(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Dispatch a JSON frame to all active sockets belonging to a user."""
        if user_id not in self.active_connections:
            return False
        
        dead_sockets = set()
        payload = json.dumps(message)
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to send to socket for user {user_id}: {e}")
                dead_sockets.add(ws)

        for ws in dead_sockets:
            self.active_connections[user_id].discard(ws)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
        return True

    async def broadcast_to_users(self, user_ids: List[str], message: Dict[str, Any]) -> None:
        """Dispatch frame to a specific list of target users if online."""
        for uid in user_ids:
            await self.send_personal_message(uid, message)

    async def calculate_badges(self, user_id: str, db: AsyncSession) -> Dict[str, int]:
        """Compute live badge counters for a user."""
        # Unread messages
        msg_stmt = (
            select(func.count(Message.id))
            .where(Message.recipient_id == user_id, Message.read_at.is_(None))
        )
        msg_res = await db.execute(msg_stmt)
        unread_messages = msg_res.scalar() or 0

        # Pending connection requests incoming
        conn_stmt = (
            select(func.count(Connection.id))
            .where(Connection.recipient_id == user_id, Connection.status == "PENDING")
        )
        conn_res = await db.execute(conn_stmt)
        pending_connections = conn_res.scalar() or 0

        # Unread notifications
        notif_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read == False)
        )
        notif_res = await db.execute(notif_stmt)
        unread_notifications = notif_res.scalar() or 0

        return {
            "unread_messages": unread_messages,
            "pending_connections": pending_connections,
            "unread_notifications": unread_notifications,
        }

    async def push_badge_update(self, user_id: str, db: AsyncSession) -> None:
        """Push badge update frame to user if online."""
        if not self.is_user_online(user_id):
            return
        badges = await self.calculate_badges(user_id, db)
        await self.send_personal_message(user_id, {
            "type": "BADGE_UPDATE",
            **badges
        })

    async def get_online_connections(self, user_id: str, db: AsyncSession) -> List[str]:
        """Get list of online 1st-degree connection user IDs for a given user."""
        stmt = (
            select(Connection)
            .where(
                or_(Connection.user_low_id == user_id, Connection.user_high_id == user_id),
                Connection.status == "ACCEPTED"
            )
        )
        result = await db.execute(stmt)
        connections = result.scalars().all()
        
        peer_ids = []
        for c in connections:
            peer_id = c.user_high_id if c.user_low_id == user_id else c.user_low_id
            if self.is_user_online(peer_id):
                peer_ids.append(peer_id)
        return peer_ids

    async def broadcast_presence(self, user_id: str, is_online: bool, db: AsyncSession) -> None:
        """Broadcast user presence state to all confirmed 1st-degree connections who are online."""
        stmt = (
            select(Connection)
            .where(
                or_(Connection.user_low_id == user_id, Connection.user_high_id == user_id),
                Connection.status == "ACCEPTED"
            )
        )
        result = await db.execute(stmt)
        connections = result.scalars().all()
        
        peer_ids = [
            c.user_high_id if c.user_low_id == user_id else c.user_low_id
            for c in connections
        ]
        
        presence_frame = {
            "type": "PRESENCE_UPDATE",
            "user_id": user_id,
            "is_online": is_online,
        }
        for peer_id in peer_ids:
            if self.is_user_online(peer_id):
                await self.send_personal_message(peer_id, presence_frame)


manager = ConnectionManager()

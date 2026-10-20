"""Social graph traversal, degree calculation (1st, 2nd, 3rd+), and mutual network evaluation."""
from typing import Tuple, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload

from app.models.schema import Connection, User, Profile
from app.schemas.contracts import DegreeType, UserSummaryDTO


class GraphService:
    """Evaluates degrees of separation and mutual connection graphs."""

    @staticmethod
    async def is_first_degree(user_a_id: str, user_b_id: str, db: AsyncSession) -> bool:
        """Check if two users share an active ACCEPTED connection edge."""
        if user_a_id == user_b_id:
            return False
        u_low = min(user_a_id, user_b_id)
        u_high = max(user_a_id, user_b_id)
        stmt = select(Connection).where(
            Connection.user_low_id == u_low,
            Connection.user_high_id == u_high,
            Connection.status == "ACCEPTED"
        )
        result = await db.execute(stmt)
        return result.scalars().first() is not None

    @staticmethod
    async def get_connection_record(user_a_id: str, user_b_id: str, db: AsyncSession) -> Optional[Connection]:
        """Fetch canonical connection edge between two users if any exists."""
        if user_a_id == user_b_id:
            return None
        u_low = min(user_a_id, user_b_id)
        u_high = max(user_a_id, user_b_id)
        stmt = select(Connection).where(
            Connection.user_low_id == u_low,
            Connection.user_high_id == u_high
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_mutual_connections(viewer_id: str, target_id: str, db: AsyncSession) -> List[UserSummaryDTO]:
        """Compute mutual 1st-degree connections between viewer and target using CTE join."""
        if viewer_id == target_id:
            return []

        sql = text("""
            WITH viewer_network AS (
                SELECT CASE WHEN user_low_id = :viewer_id THEN user_high_id ELSE user_low_id END AS friend_id
                FROM connections
                WHERE (user_low_id = :viewer_id OR user_high_id = :viewer_id)
                  AND status = 'ACCEPTED'
            ),
            target_network AS (
                SELECT CASE WHEN user_low_id = :target_id THEN user_high_id ELSE user_low_id END AS friend_id
                FROM connections
                WHERE (user_low_id = :target_id OR user_high_id = :target_id)
                  AND status = 'ACCEPTED'
            )
            SELECT u.id, u.email, u.full_name, p.headline, p.avatar_url
            FROM users u
            JOIN profiles p ON p.user_id = u.id
            JOIN viewer_network vn ON vn.friend_id = u.id
            JOIN target_network tn ON tn.friend_id = u.id
            ORDER BY u.full_name ASC;
        """)
        result = await db.execute(sql, {"viewer_id": viewer_id, "target_id": target_id})
        rows = result.fetchall()
        return [
            UserSummaryDTO(
                id=row.id,
                email=row.email,
                full_name=row.full_name,
                headline=row.headline,
                avatar_url=row.avatar_url,
            )
            for row in rows
        ]

    @staticmethod
    async def evaluate_degree_and_connection(
        viewer_id: str,
        target_id: str,
        db: AsyncSession
    ) -> Tuple[DegreeType, int, List[UserSummaryDTO], str, bool, Optional[str]]:
        """Evaluate degree of separation, mutuals, and edge state from viewer perspective."""
        if viewer_id == target_id:
            return (
                DegreeType.DEGREE_1ST,
                0,
                [],
                "SELF",
                False,
                None,
            )

        # Check existing edge
        edge = await GraphService.get_connection_record(viewer_id, target_id, db)
        connection_status = "NONE"
        viewer_initiated = False
        active_connection_id = None

        if edge:
            connection_status = edge.status
            viewer_initiated = (edge.initiator_id == viewer_id)
            active_connection_id = edge.id

        # Compute mutuals
        mutuals = await GraphService.get_mutual_connections(viewer_id, target_id, db)
        mutual_count = len(mutuals)

        # Determine degree
        if connection_status == "ACCEPTED":
            degree = DegreeType.DEGREE_1ST
        elif mutual_count > 0:
            degree = DegreeType.DEGREE_2ND
        else:
            degree = DegreeType.DEGREE_3RD_PLUS

        return (
            degree,
            mutual_count,
            mutuals,
            connection_status,
            viewer_initiated,
            active_connection_id,
        )

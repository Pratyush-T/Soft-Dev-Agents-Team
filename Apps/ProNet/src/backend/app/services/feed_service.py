"""Feed service implementing algorithmic and recent ranking with strict two-query hydration."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.models.schema import Post, PostReaction, Comment, User, Profile, Connection
from app.schemas.contracts import (
    FeedResponseDTO, PostDTO, UserSummaryDTO, CommentDTO, ReactionType
)


class FeedService:
    """Manages activity feed retrieval, ranking, and entity hydration."""

    @staticmethod
    async def get_feed(
        viewer_id: str,
        mode: str = "top",
        limit: int = 20,
        cursor: Optional[str] = None,
        db: AsyncSession = None
    ) -> FeedResponseDTO:
        """Fetch paginated feed with two-query execution to guarantee zero N+1 latency."""
        cursor_dt = None
        if cursor:
            try:
                # Support ISO 8601 timestamps
                cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            except Exception:
                cursor_dt = None

        fetch_limit = min(limit, 50) + 1  # Fetch 1 extra to accurately determine has_more

        # ----------------------------------------------------------------------
        # QUERY 1: Fetch Ranked Post IDs
        # ----------------------------------------------------------------------
        if mode == "recent":
            sql = text("""
                SELECT p.id, p.created_at
                FROM posts p
                WHERE (:cursor_created_at IS NULL OR p.created_at < :cursor_created_at)
                ORDER BY p.created_at DESC
                LIMIT :limit;
            """)
            params = {
                "cursor_created_at": cursor_dt.strftime("%Y-%m-%d %H:%M:%S.%f") if cursor_dt else None,
                "limit": fetch_limit
            }
        else:
            # Algorithmic Top Scoring
            sql = text("""
                WITH viewer_first_degrees AS (
                    SELECT CASE WHEN user_low_id = :viewer_id THEN user_high_id ELSE user_low_id END AS friend_id
                    FROM connections
                    WHERE (user_low_id = :viewer_id OR user_high_id = :viewer_id)
                      AND status = 'ACCEPTED'
                )
                SELECT 
                    p.id,
                    p.created_at,
                    (
                        ((p.like_count + p.celebrate_count + p.insightful_count) * 2.0 
                         + p.comment_count * 3.0 
                         + CASE WHEN vfd.friend_id IS NOT NULL THEN 5.0 ELSE 0.0 END)
                        / 
                        POWER(CAST(MAX(0.0, (julianday('now') - julianday(p.created_at)) * 24.0) + 2.0 AS REAL), 1.5)
                    ) AS ranking_score
                FROM posts p
                LEFT JOIN viewer_first_degrees vfd ON vfd.friend_id = p.author_id
                WHERE (:cursor_created_at IS NULL OR p.created_at < :cursor_created_at)
                ORDER BY ranking_score DESC, p.created_at DESC
                LIMIT :limit;
            """)
            params = {
                "viewer_id": viewer_id,
                "cursor_created_at": cursor_dt.strftime("%Y-%m-%d %H:%M:%S.%f") if cursor_dt else None,
                "limit": fetch_limit
            }

        res = await db.execute(sql, params)
        rows = res.fetchall()

        has_more = len(rows) > min(limit, 50)
        target_rows = rows[:min(limit, 50)]

        if not target_rows:
            return FeedResponseDTO(items=[], next_cursor=None, has_more=False)

        post_ids = [r.id for r in target_rows]
        next_cursor = target_rows[-1].created_at if has_more else None
        if next_cursor and hasattr(next_cursor, "isoformat"):
            next_cursor = next_cursor.isoformat().replace("+00:00", "Z")

        # ----------------------------------------------------------------------
        # QUERY 2: Batch Hydrate Posts, Authors, Viewer Reactions, and Comments
        # ----------------------------------------------------------------------
        posts_stmt = (
            select(Post)
            .options(
                selectinload(Post.author).selectinload(User.profile),
                selectinload(Post.comments).selectinload(Comment.author).selectinload(User.profile)
            )
            .where(Post.id.in_(post_ids))
        )
        posts_res = await db.execute(posts_stmt)
        post_map: Dict[str, Post] = {p.id: p for p in posts_res.scalars().all()}

        # Fetch viewer reactions for these posts
        reactions_stmt = (
            select(PostReaction)
            .where(PostReaction.post_id.in_(post_ids), PostReaction.user_id == viewer_id)
        )
        reactions_res = await db.execute(reactions_stmt)
        user_reaction_map: Dict[str, ReactionType] = {
            r.post_id: ReactionType(r.reaction_type) for r in reactions_res.scalars().all()
        }

        # Check 1st-degree connection status with post authors
        author_ids = list({p.author_id for p in post_map.values()})
        conn_stmt = (
            select(Connection)
            .where(
                or_(
                    and_(Connection.user_low_id == viewer_id, Connection.user_high_id.in_(author_ids)),
                    and_(Connection.user_high_id == viewer_id, Connection.user_low_id.in_(author_ids)),
                ),
                Connection.status == "ACCEPTED"
            )
        )
        conn_res = await db.execute(conn_stmt)
        connected_authors = set()
        for c in conn_res.scalars().all():
            peer = c.user_high_id if c.user_low_id == viewer_id else c.user_low_id
            connected_authors.add(peer)

        # Build PostDTOs preserving exact order of query 1
        items: List[PostDTO] = []
        for pid in post_ids:
            if pid not in post_map:
                continue
            post = post_map[pid]
            author = post.author
            profile = author.profile

            # Extract top 2 root preview comments
            root_comments = [c for c in post.comments if c.parent_id is None]
            root_comments.sort(key=lambda c: c.created_at)
            preview_comments = []
            for c in root_comments[:2]:
                c_prof = c.author.profile
                preview_comments.append(
                    CommentDTO(
                        id=c.id,
                        post_id=c.post_id,
                        author=UserSummaryDTO(
                            id=c.author.id,
                            email=c.author.email,
                            full_name=c.author.full_name,
                            headline=c_prof.headline if c_prof else "",
                            avatar_url=c_prof.avatar_url if c_prof else None,
                        ),
                        parent_id=c.parent_id,
                        content=c.content,
                        replies=[],
                        created_at=c.created_at,
                        updated_at=c.updated_at,
                    )
                )

            author_summary = UserSummaryDTO(
                id=author.id,
                email=author.email,
                full_name=author.full_name,
                headline=profile.headline if profile else "",
                avatar_url=profile.avatar_url if profile else None,
            )

            items.append(
                PostDTO(
                    id=post.id,
                    author=author_summary,
                    content=post.content,
                    code_snippet=post.code_snippet,
                    code_language=post.code_language,
                    image_url=post.image_url,
                    like_count=post.like_count,
                    celebrate_count=post.celebrate_count,
                    insightful_count=post.insightful_count,
                    comment_count=post.comment_count,
                    viewer_reaction=user_reaction_map.get(post.id),
                    is_author_connection=(author.id in connected_authors),
                    top_comments_preview=preview_comments,
                    created_at=post.created_at,
                    updated_at=post.updated_at,
                )
            )

        return FeedResponseDTO(items=items, next_cursor=next_cursor, has_more=has_more)

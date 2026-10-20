"""Activity feed, rich posts, reactions, and threaded comments API router (API-025 through API-033)."""
import uuid
import bleach
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import (
    PostNotFoundException,
    ResourceNotFoundException,
    CannotModerateCommentException,
    MaxCommentDepthExceededException,
    UnauthorizedException,
)
from app.api.deps import get_current_user
from app.models.schema import Post, PostReaction, Comment, User, Profile, Notification, Connection
from app.schemas.contracts import (
    FeedResponseDTO,
    PostDTO,
    CreatePostDTO,
    SetReactionDTO,
    ReactionResponseDTO,
    CreateCommentDTO,
    CommentDTO,
    UserSummaryDTO,
    ReactionType,
)
from app.services.feed_service import FeedService
from app.api.ws.manager import manager

router = APIRouter(tags=["Activity Feed, Posts & Comments"])

ALLOWED_HTML_TAGS = ["p", "b", "i", "strong", "em", "code", "pre", "br", "ul", "ol", "li", "a"]
ALLOWED_HTML_ATTRS = {"a": ["href", "title", "target"]}


def sanitize_text(text: str) -> str:
    """Sanitize user text input with bleach to prevent XSS while allowing basic markdown tags."""
    if not text:
        return ""
    return bleach.clean(text.strip(), tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRS, strip=True)


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


# ==============================================================================
# FEED & POSTS
# ==============================================================================

@router.get("/feed", response_model=FeedResponseDTO, status_code=status.HTTP_200_OK)
async def get_feed(
    mode: str = Query("top", pattern="^(recent|top)$"),
    limit: int = Query(20, ge=1, le=50),
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-025: Retrieve paginated dual-mode activity feed (recent or top)."""
    return await FeedService.get_feed(
        viewer_id=current_user.id,
        mode=mode,
        limit=limit,
        cursor=cursor,
        db=db,
    )


@router.post("/posts", response_model=PostDTO, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: CreatePostDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-026: Create rich post with formatted text, code snippet, or media."""
    sanitized_content = sanitize_text(body.content)
    post_id = f"post_{uuid.uuid4().hex[:12]}"

    post = Post(
        id=post_id,
        author_id=current_user.id,
        content=sanitized_content,
        code_snippet=body.code_snippet,
        code_language=body.code_language,
        image_url=body.image_url,
        like_count=0,
        celebrate_count=0,
        insightful_count=0,
        comment_count=0,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return PostDTO(
        id=post.id,
        author=format_user_summary(current_user),
        content=post.content,
        code_snippet=post.code_snippet,
        code_language=post.code_language,
        image_url=post.image_url,
        like_count=0,
        celebrate_count=0,
        insightful_count=0,
        comment_count=0,
        viewer_reaction=None,
        is_author_connection=False,
        top_comments_preview=[],
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("/posts/{post_id}", response_model=PostDTO, status_code=status.HTTP_200_OK)
async def get_post_detail(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-027: Retrieve single post detail with hydrated author, counts, and reactions."""
    stmt = (
        select(Post)
        .options(
            selectinload(Post.author).selectinload(User.profile),
            selectinload(Post.comments).selectinload(Comment.author).selectinload(User.profile),
        )
        .where(Post.id == post_id)
    )
    res = await db.execute(stmt)
    post = res.scalars().first()
    if not post:
        raise PostNotFoundException()

    # Get viewer reaction
    react_stmt = select(PostReaction).where(
        PostReaction.post_id == post_id,
        PostReaction.user_id == current_user.id
    )
    react_res = await db.execute(react_stmt)
    active_reaction = react_res.scalars().first()

    # Check connection
    u_low = min(current_user.id, post.author_id)
    u_high = max(current_user.id, post.author_id)
    conn_stmt = select(Connection).where(
        Connection.user_low_id == u_low,
        Connection.user_high_id == u_high,
        Connection.status == "ACCEPTED"
    )
    conn_res = await db.execute(conn_stmt)
    is_connected = conn_res.scalars().first() is not None

    root_comments = [c for c in post.comments if c.parent_id is None]
    root_comments.sort(key=lambda c: c.created_at)
    preview = [
        CommentDTO(
            id=c.id,
            post_id=c.post_id,
            author=format_user_summary(c.author),
            parent_id=c.parent_id,
            content=c.content,
            replies=[],
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in root_comments[:2]
    ]

    return PostDTO(
        id=post.id,
        author=format_user_summary(post.author),
        content=post.content,
        code_snippet=post.code_snippet,
        code_language=post.code_language,
        image_url=post.image_url,
        like_count=post.like_count,
        celebrate_count=post.celebrate_count,
        insightful_count=post.insightful_count,
        comment_count=post.comment_count,
        viewer_reaction=ReactionType(active_reaction.reaction_type) if active_reaction else None,
        is_author_connection=is_connected,
        top_comments_preview=preview,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-028: Delete post (author only)."""
    post = await db.get(Post, post_id)
    if not post:
        raise PostNotFoundException()

    if post.author_id != current_user.id:
        raise UnauthorizedException("You do not have permission to delete this post.")

    await db.delete(post)
    await db.commit()
    return None


# ==============================================================================
# REACTIONS
# ==============================================================================

@router.post("/posts/{post_id}/reactions", response_model=ReactionResponseDTO, status_code=status.HTTP_200_OK)
async def toggle_post_reaction(
    post_id: str,
    body: SetReactionDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-029: Toggle or switch emotional reaction (LIKE, CELEBRATE, INSIGHTFUL)."""
    post = await db.get(Post, post_id)
    if not post:
        raise PostNotFoundException()

    target_type = body.reaction_type.value

    stmt = select(PostReaction).where(
        PostReaction.post_id == post_id,
        PostReaction.user_id == current_user.id
    )
    res = await db.execute(stmt)
    existing_reaction = res.scalars().first()

    active_reaction = None

    if existing_reaction:
        if existing_reaction.reaction_type == target_type:
            # Toggle OFF
            if target_type == "LIKE":
                post.like_count = max(0, post.like_count - 1)
            elif target_type == "CELEBRATE":
                post.celebrate_count = max(0, post.celebrate_count - 1)
            elif target_type == "INSIGHTFUL":
                post.insightful_count = max(0, post.insightful_count - 1)
            await db.delete(existing_reaction)
            active_reaction = None
        else:
            # Switch reaction
            old_type = existing_reaction.reaction_type
            if old_type == "LIKE":
                post.like_count = max(0, post.like_count - 1)
            elif old_type == "CELEBRATE":
                post.celebrate_count = max(0, post.celebrate_count - 1)
            elif old_type == "INSIGHTFUL":
                post.insightful_count = max(0, post.insightful_count - 1)

            if target_type == "LIKE":
                post.like_count += 1
            elif target_type == "CELEBRATE":
                post.celebrate_count += 1
            elif target_type == "INSIGHTFUL":
                post.insightful_count += 1

            existing_reaction.reaction_type = target_type
            active_reaction = ReactionType(target_type)
    else:
        # Create new reaction
        new_react = PostReaction(
            id=f"react_{uuid.uuid4().hex[:12]}",
            post_id=post_id,
            user_id=current_user.id,
            reaction_type=target_type,
        )
        db.add(new_react)

        if target_type == "LIKE":
            post.like_count += 1
        elif target_type == "CELEBRATE":
            post.celebrate_count += 1
        elif target_type == "INSIGHTFUL":
            post.insightful_count += 1
        active_reaction = ReactionType(target_type)

        # Notify post author if not self
        if post.author_id != current_user.id:
            notif = Notification(
                id=f"notif_{uuid.uuid4().hex[:12]}",
                user_id=post.author_id,
                actor_id=current_user.id,
                notification_type="POST_REACTION",
                title="New Reaction",
                content=f"{current_user.full_name} reacted to your post.",
                reference_id=post.id,
                reference_type="POST",
                is_read=False,
            )
            db.add(notif)

    await db.commit()
    await db.refresh(post)

    if post.author_id != current_user.id:
        await manager.push_badge_update(post.author_id, db)

    return ReactionResponseDTO(
        active_reaction=active_reaction,
        like_count=post.like_count,
        celebrate_count=post.celebrate_count,
        insightful_count=post.insightful_count,
    )


@router.delete("/posts/{post_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def remove_post_reaction(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-030: Remove emotional reaction from post."""
    post = await db.get(Post, post_id)
    if not post:
        raise PostNotFoundException()

    stmt = select(PostReaction).where(
        PostReaction.post_id == post_id,
        PostReaction.user_id == current_user.id
    )
    res = await db.execute(stmt)
    react = res.scalars().first()
    if react:
        if react.reaction_type == "LIKE":
            post.like_count = max(0, post.like_count - 1)
        elif react.reaction_type == "CELEBRATE":
            post.celebrate_count = max(0, post.celebrate_count - 1)
        elif react.reaction_type == "INSIGHTFUL":
            post.insightful_count = max(0, post.insightful_count - 1)
        await db.delete(react)
        await db.commit()

    return None


# ==============================================================================
# THREADED COMMENTS (2-LEVEL HIERARCHY)
# ==============================================================================

@router.get("/posts/{post_id}/comments", response_model=List[CommentDTO], status_code=status.HTTP_200_OK)
async def list_post_comments(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-031: List 2-level threaded comments for post."""
    stmt = (
        select(Comment)
        .options(selectinload(Comment.author).selectinload(User.profile))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    )
    res = await db.execute(stmt)
    all_comments = res.scalars().all()

    # Structure into 2-level tree
    root_comments: List[CommentDTO] = []
    replies_map: Dict[str, List[CommentDTO]] = {}

    for c in all_comments:
        dto = CommentDTO(
            id=c.id,
            post_id=c.post_id,
            author=format_user_summary(c.author),
            parent_id=c.parent_id,
            content=c.content,
            replies=[],
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        if c.parent_id is None:
            root_comments.append(dto)
        else:
            if c.parent_id not in replies_map:
                replies_map[c.parent_id] = []
            replies_map[c.parent_id].append(dto)

    for root in root_comments:
        root.replies = replies_map.get(root.id, [])

    return root_comments


@router.post("/posts/{post_id}/comments", response_model=CommentDTO, status_code=status.HTTP_201_CREATED)
async def add_comment(
    post_id: str,
    body: CreateCommentDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-032: Add root comment or nested Level 2 reply to post."""
    post = await db.get(Post, post_id)
    if not post:
        raise PostNotFoundException()

    sanitized_content = sanitize_text(body.content)

    parent_comment = None
    if body.parent_id:
        parent_comment = await db.get(Comment, body.parent_id)
        if not parent_comment or parent_comment.post_id != post_id:
            raise ResourceNotFoundException("Target parent comment not found on this post.")
        if parent_comment.parent_id is not None:
            # Depth > 2 blocked
            raise MaxCommentDepthExceededException()

    cmt_id = f"cmt_{uuid.uuid4().hex[:12]}"
    comment = Comment(
        id=cmt_id,
        post_id=post_id,
        author_id=current_user.id,
        parent_id=body.parent_id,
        content=sanitized_content,
    )
    db.add(comment)

    # Increment post comment count
    post.comment_count += 1

    # Dispatch notification
    notif_target_id = None
    notif_type = None
    if parent_comment and parent_comment.author_id != current_user.id:
        notif_target_id = parent_comment.author_id
        notif_type = "COMMENT_REPLY"
        notif_title = "New Reply"
        notif_text = f"{current_user.full_name} replied to your comment."
    elif not body.parent_id and post.author_id != current_user.id:
        notif_target_id = post.author_id
        notif_type = "POST_COMMENT"
        notif_title = "New Comment"
        notif_text = f"{current_user.full_name} commented on your post."

    if notif_target_id:
        notif = Notification(
            id=f"notif_{uuid.uuid4().hex[:12]}",
            user_id=notif_target_id,
            actor_id=current_user.id,
            notification_type=notif_type,
            title=notif_title,
            content=notif_text,
            reference_id=post.id,
            reference_type="POST",
            is_read=False,
        )
        db.add(notif)

    await db.commit()
    await db.refresh(comment)

    if notif_target_id:
        await manager.push_badge_update(notif_target_id, db)

    return CommentDTO(
        id=comment.id,
        post_id=comment.post_id,
        author=format_user_summary(current_user),
        parent_id=comment.parent_id,
        content=comment.content,
        replies=[],
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-033: Delete comment (permitted for comment author or post author)."""
    stmt = (
        select(Comment)
        .options(selectinload(Comment.post), selectinload(Comment.replies))
        .where(Comment.id == comment_id)
    )
    res = await db.execute(stmt)
    comment = res.scalars().first()
    if not comment:
        raise ResourceNotFoundException("Comment not found.")

    post = comment.post
    if comment.author_id != current_user.id and post.author_id != current_user.id:
        raise CannotModerateCommentException()

    # Decrement post comment counter by 1 + len(replies)
    deleted_count = 1 + len(comment.replies)
    post.comment_count = max(0, post.comment_count - deleted_count)

    await db.delete(comment)
    await db.commit()
    return None

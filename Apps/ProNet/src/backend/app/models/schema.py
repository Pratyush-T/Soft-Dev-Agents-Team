"""SQLAlchemy 2.0 ORM Declarative Models for ProNet."""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base model."""



# ==============================================================================
# 1. IDENTITY & PROFILE DOMAIN
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    profile: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    experiences: Mapped[List["Experience"]] = relationship("Experience", back_populates="user", cascade="all, delete-orphan", order_by="desc(Experience.start_date)")
    educations: Mapped[List["Education"]] = relationship("Education", back_populates="user", cascade="all, delete-orphan", order_by="desc(Education.start_year)")
    user_skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    reactions: Mapped[List["PostReaction"]] = relationship("PostReaction", back_populates="user", cascade="all, delete-orphan")
    jobs_posted: Mapped[List["Job"]] = relationship("Job", back_populates="poster", cascade="all, delete-orphan")
    job_applications: Mapped[List["JobApplication"]] = relationship("JobApplication", back_populates="applicant", cascade="all, delete-orphan")
    notifications_received: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", foreign_keys="[Notification.user_id]", cascade="all, delete-orphan")
    notifications_triggered: Mapped[List["Notification"]] = relationship("Notification", back_populates="actor", foreign_keys="[Notification.actor_id]", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    connections_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")

    __table_args__ = (
        CheckConstraint("connections_count >= 0", name="chk_profile_connections_count_positive"),
    )


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    company: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="experiences")

    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="chk_experience_dates_consistent"),
        Index("ix_experiences_user_dates", "user_id", "start_date"),
    )


class Education(Base):
    __tablename__ = "educations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    institution: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    degree: Mapped[str] = mapped_column(String(128), nullable=False)
    field_of_study: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="educations")

    __table_args__ = (
        CheckConstraint("end_year IS NULL OR end_year >= start_year", name="chk_education_years_consistent"),
        Index("ix_educations_user_years", "user_id", "start_year"),
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user_skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="user_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="user_skills")

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill_pair"),
        Index("ix_user_skills_composite", "user_id", "skill_id"),
    )


# ==============================================================================
# 2. SOCIAL GRAPH DOMAIN (CONNECTIONS)
# ==============================================================================

class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_low_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    user_high_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    initiator_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # PENDING, ACCEPTED, IGNORED
    note: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user_low: Mapped["User"] = relationship("User", foreign_keys=[user_low_id])
    user_high: Mapped["User"] = relationship("User", foreign_keys=[user_high_id])
    initiator: Mapped["User"] = relationship("User", foreign_keys=[initiator_id])
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id])

    __table_args__ = (
        CheckConstraint("user_low_id < user_high_id", name="chk_connection_canonical_order"),
        CheckConstraint("status IN ('PENDING', 'ACCEPTED', 'IGNORED')", name="chk_connection_status_valid"),
        CheckConstraint(
            "initiator_id IN (user_low_id, user_high_id) AND recipient_id IN (user_low_id, user_high_id) AND initiator_id != recipient_id",
            name="chk_connection_parties_consistent"
        ),
        UniqueConstraint("user_low_id", "user_high_id", name="uq_connection_canonical_pair"),
        Index("ix_connections_low_status", "user_low_id", "status"),
        Index("ix_connections_high_status", "user_high_id", "status"),
        Index("ix_connections_recipient_status", "recipient_id", "status"),
        Index("ix_connections_initiator_status", "initiator_id", "status"),
    )


# ==============================================================================
# 3. ACTIVITY FEED, REACTIONS & THREADED COMMENTS
# ==============================================================================

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    author_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code_language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    celebrate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    insightful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    author: Mapped["User"] = relationship("User", back_populates="posts")
    reactions: Mapped[List["PostReaction"]] = relationship("PostReaction", back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("like_count >= 0", name="chk_post_likes_positive"),
        CheckConstraint("celebrate_count >= 0", name="chk_post_celebrates_positive"),
        CheckConstraint("insightful_count >= 0", name="chk_post_insights_positive"),
        CheckConstraint("comment_count >= 0", name="chk_post_comments_positive"),
        Index("ix_posts_author_created", "author_id", "created_at"),
        Index("ix_posts_feed_pagination", "created_at", "id"),
    )


class PostReaction(Base):
    __tablename__ = "post_reactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(64), ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    reaction_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # LIKE, CELEBRATE, INSIGHTFUL
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    post: Mapped["Post"] = relationship("Post", back_populates="reactions")
    user: Mapped["User"] = relationship("User", back_populates="reactions")

    __table_args__ = (
        CheckConstraint("reaction_type IN ('LIKE', 'CELEBRATE', 'INSIGHTFUL')", name="chk_reaction_type_valid"),
        UniqueConstraint("post_id", "user_id", name="uq_post_user_reaction"),
        Index("ix_post_reactions_post_type", "post_id", "reaction_type"),
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(64), ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False)
    author_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("comments.id", ondelete="CASCADE"), index=True, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
    parent: Mapped[Optional["Comment"]] = relationship("Comment", remote_side=[id], back_populates="replies")
    replies: Mapped[List["Comment"]] = relationship("Comment", back_populates="parent", cascade="all, delete-orphan", order_by="Comment.created_at.asc()")

    __table_args__ = (
        Index("ix_comments_post_parent_created", "post_id", "parent_id", "created_at"),
    )


# ==============================================================================
# 4. JOB BOARD & MINI-ATS DOMAIN
# ==============================================================================

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    poster_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    workplace_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # REMOTE, HYBRID, ON_SITE
    location: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    salary_min: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_max: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded array: ["Python", "FastAPI"]
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True, nullable=False)  # OPEN, CLOSED
    application_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    poster: Mapped["User"] = relationship("User", back_populates="jobs_posted")
    applications: Mapped[List["JobApplication"]] = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("workplace_type IN ('REMOTE', 'HYBRID', 'ON_SITE')", name="chk_job_workplace_type"),
        CheckConstraint("status IN ('OPEN', 'CLOSED')", name="chk_job_status_valid"),
        CheckConstraint("salary_max >= salary_min", name="chk_job_salary_consistent"),
        CheckConstraint("application_count >= 0", name="chk_job_applications_positive"),
        Index("ix_jobs_filter_workplace_status", "status", "workplace_type", "created_at"),
        Index("ix_jobs_poster_created", "poster_id", "created_at"),
    )


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    applicant_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="APPLIED", index=True, nullable=False)  # APPLIED, REVIEWING, SHORTLISTED, REJECTED
    cover_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resume_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    profile_headline_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    skills_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    applicant: Mapped["User"] = relationship("User", back_populates="job_applications")

    __table_args__ = (
        CheckConstraint("status IN ('APPLIED', 'REVIEWING', 'SHORTLISTED', 'REJECTED')", name="chk_application_status_valid"),
        UniqueConstraint("job_id", "applicant_id", name="uq_job_applicant_pair"),
        Index("ix_job_applications_pipeline", "job_id", "status", "created_at"),
        Index("ix_job_applications_applicant", "applicant_id", "created_at"),
    )


# ==============================================================================
# 5. REAL-TIME DIRECT MESSAGING & NOTIFICATIONS
# ==============================================================================

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sender_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)

    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id])

    __table_args__ = (
        Index("ix_messages_conversation_history", "sender_id", "recipient_id", "created_at"),
        Index("ix_messages_unread_badge", "recipient_id", "read_at"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="notifications_received")
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id], back_populates="notifications_triggered")

    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('CONNECTION_REQUEST', 'CONNECTION_ACCEPTED', 'POST_REACTION', 'POST_COMMENT', 'COMMENT_REPLY', 'JOB_STATUS_CHANGE', 'NEW_MESSAGE')",
            name="chk_notification_type_valid"
        ),
        CheckConstraint(
            "reference_type IS NULL OR reference_type IN ('POST', 'JOB', 'CONNECTION', 'MESSAGE')",
            name="chk_notification_reference_type"
        ),
        Index("ix_notifications_unread_user", "user_id", "is_read", "created_at"),
    )

"""Pydantic v2 schemas and validation models matching 04_api_contracts.md."""
import email_validator
if hasattr(email_validator, "SPECIAL_USE_DOMAIN_NAMES") and "local" in email_validator.SPECIAL_USE_DOMAIN_NAMES:
    email_validator.SPECIAL_USE_DOMAIN_NAMES.remove("local")

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, EmailStr, model_validator, ConfigDict


# ==============================================================================
# ENUMERATIONS
# ==============================================================================

class DegreeType(str, Enum):
    DEGREE_1ST = "1st"
    DEGREE_2ND = "2nd"
    DEGREE_3RD_PLUS = "3rd+"


class ConnectionStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    IGNORED = "IGNORED"


class WorkplaceType(str, Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ON_SITE = "ON_SITE"


class JobStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ApplicationStatus(str, Enum):
    APPLIED = "APPLIED"
    REVIEWING = "REVIEWING"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"


class ReactionType(str, Enum):
    LIKE = "LIKE"
    CELEBRATE = "CELEBRATE"
    INSIGHTFUL = "INSIGHTFUL"


class FeedMode(str, Enum):
    RECENT = "recent"
    TOP = "top"


class NotificationType(str, Enum):
    CONNECTION_REQUEST = "CONNECTION_REQUEST"
    CONNECTION_ACCEPTED = "CONNECTION_ACCEPTED"
    POST_REACTION = "POST_REACTION"
    POST_COMMENT = "POST_COMMENT"
    COMMENT_REPLY = "COMMENT_REPLY"
    JOB_STATUS_CHANGE = "JOB_STATUS_CHANGE"
    NEW_MESSAGE = "NEW_MESSAGE"


class ReferenceType(str, Enum):
    POST = "POST"
    JOB = "JOB"
    CONNECTION = "CONNECTION"
    MESSAGE = "MESSAGE"


# ==============================================================================
# ERROR SCHEMAS
# ==============================================================================

class ErrorDetailBody(BaseModel):
    code: str = Field(..., description="Unique machine-readable error token (e.g., ERR-001 or CODE)")
    message: str = Field(..., description="Human-readable English description of the failure condition")
    status_code: int = Field(..., description="HTTP status integer matching the response header")
    timestamp: datetime = Field(..., description="UTC ISO-8601 timestamp when exception was handled")
    path: str = Field(..., description="Request path matching URI")
    request_id: str = Field(..., description="Request correlation identifier")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Structured failure context")


class ErrorEnvelope(BaseModel):
    error: ErrorDetailBody


# ==============================================================================
# PAGINATION GENERIC
# ==============================================================================

T = TypeVar("T")

class CursorPaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    next_cursor: Optional[str] = None
    has_more: bool
    total_count: Optional[int] = None


# ==============================================================================
# AUTH & PERSONA SCHEMAS
# ==============================================================================

class PersonaDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=128)
    headline: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=128)
    avatar_url: Optional[str] = Field(None, max_length=512)

    model_config = ConfigDict(from_attributes=True)


class UserSummaryDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=128)
    headline: str = Field(..., min_length=1, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=512)

    model_config = ConfigDict(from_attributes=True)


class AuthTokensDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 86400
    user: UserSummaryDTO


class RegisterRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password, length >= 8")
    full_name: str = Field(..., min_length=2, max_length=128)
    headline: str = Field(..., min_length=2, max_length=255)
    location: str = Field(..., min_length=2, max_length=128)


class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class QuickSwitchRequestDTO(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)


# ==============================================================================
# PROFILE & USER SCHEMAS
# ==============================================================================

class ProfileDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    user_id: str = Field(..., min_length=1, max_length=64)
    headline: str = Field(..., max_length=255)
    bio: Optional[str] = None
    location: str = Field(..., max_length=128)
    avatar_url: Optional[str] = Field(None, max_length=512)
    connections_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateDTO(BaseModel):
    headline: Optional[str] = Field(None, min_length=2, max_length=255)
    bio: Optional[str] = Field(None, max_length=5000)
    location: Optional[str] = Field(None, min_length=2, max_length=128)
    avatar_url: Optional[str] = Field(None, max_length=512)


class ExperienceDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    user_id: str = Field(..., min_length=1, max_length=64)
    company: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    location: Optional[str] = Field(None, max_length=128)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperienceCreateDTO(BaseModel):
    company: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    location: Optional[str] = Field(None, max_length=128)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = Field(None, max_length=4000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceCreateDTO":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("END_DATE_BEFORE_START_DATE")
        if self.is_current and self.end_date is not None:
            self.end_date = None
        return self


class ExperienceUpdateDTO(ExperienceCreateDTO):
    """Experience update request schema inheriting create attributes."""


class EducationDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    user_id: str = Field(..., min_length=1, max_length=64)
    institution: str = Field(..., min_length=1, max_length=128)
    degree: str = Field(..., min_length=1, max_length=128)
    field_of_study: Optional[str] = Field(None, max_length=128)
    start_year: int = Field(ge=1900, le=2100)
    end_year: Optional[int] = Field(None, ge=1900, le=2100)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EducationCreateDTO(BaseModel):
    institution: str = Field(..., min_length=1, max_length=128)
    degree: str = Field(..., min_length=1, max_length=128)
    field_of_study: Optional[str] = Field(None, max_length=128)
    start_year: int = Field(ge=1900, le=2100)
    end_year: Optional[int] = Field(None, ge=1900, le=2100)

    @model_validator(mode="after")
    def validate_years(self) -> "EducationCreateDTO":
        if self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("END_DATE_BEFORE_START_DATE")
        return self


class EducationUpdateDTO(EducationCreateDTO):
    """Education update request schema inheriting create attributes."""



class SkillDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=64)
    category: Optional[str] = Field(None, max_length=64)

    model_config = ConfigDict(from_attributes=True)


class UserSkillAddDTO(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=64)


class ProfileDetailDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    full_name: str
    profile: ProfileDTO
    degree: DegreeType
    mutual_connections_count: int = Field(ge=0)
    mutual_connections_preview: List[UserSummaryDTO] = Field(default_factory=list)
    experiences: List[ExperienceDTO] = Field(default_factory=list)
    educations: List[EducationDTO] = Field(default_factory=list)
    skills: List[SkillDTO] = Field(default_factory=list)
    connection_status_with_viewer: str = Field(..., description="PENDING | ACCEPTED | IGNORED | NONE | SELF")
    viewer_initiated_connection: bool = False
    active_connection_id: Optional[str] = None


# ==============================================================================
# SOCIAL GRAPH & CONNECTIONS SCHEMAS
# ==============================================================================

class ConnectionDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    user_low_id: str
    user_high_id: str
    initiator_id: str
    recipient_id: str
    status: ConnectionStatus
    note: Optional[str] = Field(None, max_length=300)
    created_at: datetime
    updated_at: datetime
    peer: UserSummaryDTO

    model_config = ConfigDict(from_attributes=True)


class PendingConnectionsDTO(BaseModel):
    incoming: List[ConnectionDTO] = Field(default_factory=list)
    outgoing: List[ConnectionDTO] = Field(default_factory=list)


class SendConnectionRequestDTO(BaseModel):
    recipient_id: str = Field(..., min_length=1, max_length=64)
    note: Optional[str] = Field(None, max_length=300)


# ==============================================================================
# ACTIVITY FEED, REACTIONS & COMMENTS SCHEMAS
# ==============================================================================

class CreatePostDTO(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000)
    code_snippet: Optional[str] = Field(None, max_length=10000)
    code_language: Optional[str] = Field(None, max_length=32)
    image_url: Optional[str] = Field(None, max_length=512)


class SetReactionDTO(BaseModel):
    reaction_type: ReactionType


class ReactionResponseDTO(BaseModel):
    active_reaction: Optional[ReactionType] = None
    like_count: int = Field(ge=0)
    celebrate_count: int = Field(ge=0)
    insightful_count: int = Field(ge=0)


class CreateCommentDTO(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[str] = Field(None, max_length=64)


class CommentDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    post_id: str
    author: UserSummaryDTO
    parent_id: Optional[str] = None
    content: str
    replies: List["CommentDTO"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    author: UserSummaryDTO
    content: str
    code_snippet: Optional[str] = None
    code_language: Optional[str] = None
    image_url: Optional[str] = None
    like_count: int = Field(ge=0)
    celebrate_count: int = Field(ge=0)
    insightful_count: int = Field(ge=0)
    comment_count: int = Field(ge=0)
    viewer_reaction: Optional[ReactionType] = None
    is_author_connection: bool = False
    top_comments_preview: List[CommentDTO] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedResponseDTO(BaseModel):
    items: List[PostDTO]
    next_cursor: Optional[str] = None
    has_more: bool


# ==============================================================================
# JOBS & ATS PIPELINE SCHEMAS
# ==============================================================================

class CreateJobDTO(BaseModel):
    title: str = Field(..., min_length=3, max_length=128)
    company_name: str = Field(..., min_length=2, max_length=128)
    workplace_type: WorkplaceType
    location: str = Field(..., min_length=2, max_length=128)
    salary_min: int = Field(ge=0)
    salary_max: int = Field(ge=0)
    description: str = Field(..., min_length=10, max_length=20000)
    required_skills: List[str] = Field(..., min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_salaries(self) -> "CreateJobDTO":
        if self.salary_max < self.salary_min:
            raise ValueError("SALARY_MAX_MUST_EXCEED_MIN")
        return self


class UpdateJobStatusDTO(BaseModel):
    status: JobStatus


class JobDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    poster: UserSummaryDTO
    title: str
    company_name: str
    workplace_type: WorkplaceType
    location: str
    salary_min: int
    salary_max: int
    description: str
    required_skills: List[str]
    status: JobStatus
    application_count: int = Field(ge=0)
    has_viewer_applied: bool = False
    viewer_application_status: Optional[ApplicationStatus] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EasyApplyDTO(BaseModel):
    cover_note: Optional[str] = Field(None, max_length=500)
    resume_url: Optional[str] = Field(None, max_length=512)


class JobApplicationDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    job_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    applicant: UserSummaryDTO
    status: ApplicationStatus
    cover_note: Optional[str] = None
    resume_url: Optional[str] = None
    profile_headline_snapshot: str
    skills_snapshot: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateApplicationStatusDTO(BaseModel):
    status: ApplicationStatus


# ==============================================================================
# MESSAGING & NOTIFICATIONS SCHEMAS
# ==============================================================================

class MessageDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    sender_id: str
    recipient_id: str
    content: str
    read_at: Optional[datetime] = None
    created_at: datetime
    is_outgoing: bool = False

    model_config = ConfigDict(from_attributes=True)


class ConversationSummaryDTO(BaseModel):
    peer: UserSummaryDTO
    last_message: MessageDTO
    unread_count: int = Field(ge=0)


class MarkConversationReadResponseDTO(BaseModel):
    marked_count: int = Field(ge=0)


class NotificationDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    user_id: str
    actor: UserSummaryDTO
    notification_type: NotificationType
    title: str = Field(..., max_length=128)
    content: str = Field(..., max_length=255)
    reference_id: Optional[str] = None
    reference_type: Optional[ReferenceType] = None
    is_read: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarkNotificationsReadRequestDTO(BaseModel):
    notification_ids: Optional[List[str]] = None


class MarkNotificationsReadResponseDTO(BaseModel):
    success: bool = True
    marked_count: int = Field(ge=0)


class BadgeCountsDTO(BaseModel):
    unread_messages: int = Field(ge=0)
    pending_connections: int = Field(ge=0)
    unread_notifications: int = Field(ge=0)


class UploadResponseDTO(BaseModel):
    file_url: str = Field(..., max_length=512)
    file_name: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=128)
    size_bytes: int = Field(gt=0)

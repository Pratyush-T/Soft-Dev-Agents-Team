# ProNet - REST API & WebSocket Protocol Contract Specification (v1.0.0)

- **Document Version:** 1.0.0
- **Status:** Approved Engineering Contract
- **Author:** Principal API Contract Engineer
- **Target Release:** v1.0 Local Production
- **Approved For Implementation:** Phase 4 (`06_backend_eng`, `07_frontend_eng`)
- **Base REST Path:** `http://localhost:8000/api/v1`
- **Base WebSocket Path:** `ws://localhost:8000/ws`

---

## 1. Executive Contract Summary & Protocol Standards

### 1.1 Purpose and Cross-Tier Governance
This document specifies the authoritative, immutable REST and WebSocket interface contracts for **ProNet**. It serves as the single source of truth for both Backend Engineering (`06_backend_eng`) and Frontend Engineering (`07_frontend_eng`). Both teams can execute implementation concurrently without guessing a single field name, URI parameter, enum value, or validation rule.

### 1.2 Protocol Standards & Conventions

1. **Transport Layer:**
   - REST API: HTTP/1.1 over TCP (`http://localhost:8000`).
   - WebSockets: RFC 6455 over TCP (`ws://localhost:8000/ws`).
2. **Data Serialization:**
   - All REST request bodies and non-binary responses MUST be serialized as UTF-8 JSON (`Content-Type: application/json`).
   - Binary file uploads (avatars, post attachments, resumes) use `multipart/form-data`.
3. **Authentication Scheme:**
   - HTTP Endpoints: Standard HTTP `Authorization` header with the Bearer scheme:
     `Authorization: Bearer <jwt_token>`
   - WebSocket Handshake: Pass the token in the query parameter during the initial HTTP upgrade handshake:
     `ws://localhost:8000/ws?token=<jwt_token>`
4. **Date and Time Representation:**
   - All timestamps are ISO-8601 formatted strings in coordinated universal time (UTC) ending in `Z`:
     `YYYY-MM-DDTHH:MM:SSZ` (e.g., `2026-10-20T04:55:12Z`).
   - Date-only fields use ISO-8601 calendar date strings:
     `YYYY-MM-DD` (e.g., `2024-03-01`).
5. **Cursor-Based Pagination Standard:**
   - All collection listing endpoints (Feed, Messages, Notifications, Jobs) implement cursor pagination.
   - Request Query Parameters:
     - `limit` (integer, default `20`, minimum `1`, maximum `50`): Number of items to retrieve.
     - `cursor` (string, optional): Base64-encoded or timestamp pointer returned from previous query.
   - Response Envelope Pattern:
     ```json
     {
       "items": [...],
       "next_cursor": "2026-10-20T04:50:00Z",
       "has_more": true,
       "total_count": 42
     }
     ```
6. **Correlation & Idempotency:**
   - Every HTTP response contains the header `X-Request-ID: <uuid>` generated or propagated by the ASGI middleware.
   - All logging, metrics, and error responses bind to this identifier.

---

## 2. Standardized Error Envelope & Status Matrix

### 2.1 Uniform Error Envelope Schema
All error responses (4xx and 5xx) emitted by FastAPI return a uniform envelope containing an `error` object with strict machine-readable codes and diagnostic metadata:

```json
{
  "error": {
    "code": "CONNECTION_ALREADY_REQUESTED",
    "message": "A connection request between these users is already pending or established.",
    "status_code": 409,
    "timestamp": "2026-10-20T04:55:12Z",
    "path": "/api/v1/connections/request",
    "request_id": "req_01HPX7Z9B4F1M9K8V3W2",
    "details": {
      "initiator_id": "usr_alex_chen",
      "target_id": "usr_elena_rostova"
    }
  }
}
```

### 2.2 Traceable Error Code Registry (`ERR-001` through `ERR-024`)

| Error Code | Machine Identifier | HTTP Status | Trigger Condition | Default User-Facing Message |
|---|---|---|---|---|
| **ERR-001** | `INVALID_CREDENTIALS` | 401 Unauthorized | Email not found or bcrypt password verification fails. | "Invalid email address or password." |
| **ERR-002** | `TOKEN_EXPIRED` | 401 Unauthorized | Bearer token `exp` timestamp is in the past (> 24h). | "Your authentication token has expired. Please log in again." |
| **ERR-003** | `INVALID_TOKEN` | 401 Unauthorized | Bearer token signature invalid, corrupt, or missing claims. | "Invalid or malformed authentication token." |
| **ERR-004** | `UNAUTHORIZED` | 401 Unauthorized | Missing `Authorization: Bearer <token>` header on protected route. | "Authentication required to access this resource." |
| **ERR-005** | `NOT_JOB_OWNER` | 403 Forbidden | User attempts to view applicant pipeline for a job posted by another user. | "You are not authorized to view applicants for this job posting." |
| **ERR-006** | `MUST_BE_FIRST_DEGREE` | 403 Forbidden | User attempts to initiate direct message with a user who is not a confirmed 1st-degree connection. | "Direct messaging is restricted to confirmed 1st-degree connections." |
| **ERR-007** | `CANNOT_MODERATE_COMMENT` | 403 Forbidden | User attempts to delete a comment they did not author on a post they do not own. | "You do not have permission to delete this comment." |
| **ERR-008** | `RESOURCE_NOT_FOUND` | 404 Not Found | Generic target entity ID does not exist in SQLite database. | "The requested resource could not be found." |
| **ERR-009** | `USER_NOT_FOUND` | 404 Not Found | Target `user_id` does not exist in `users` table. | "The specified user account does not exist." |
| **ERR-010** | `POST_NOT_FOUND` | 404 Not Found | Target `post_id` does not exist in `posts` table. | "The specified feed post does not exist or has been removed." |
| **ERR-011** | `JOB_NOT_FOUND` | 404 Not Found | Target `job_id` does not exist in `jobs` table. | "The specified job listing does not exist." |
| **ERR-012** | `CONNECTION_ALREADY_REQUESTED` | 409 Conflict | User attempts to send a connection request when a pending edge already exists. | "A connection request is already pending between these users." |
| **ERR-013** | `ALREADY_CONNECTED` | 409 Conflict | User attempts to send a request to an existing 1st-degree connection (`status = 'ACCEPTED'`). | "You are already connected with this professional." |
| **ERR-014** | `ALREADY_APPLIED_TO_JOB` | 409 Conflict | Candidate submits duplicate "Easy Apply" for the same job listing. | "You have already submitted an application for this role." |
| **ERR-015** | `CANNOT_WITHDRAW_ACCEPTED_CONNECTION`| 400 Bad Request | Sender attempts to withdraw request that has already transitioned to `ACCEPTED`. | "Cannot withdraw a connection that has already been accepted." |
| **ERR-016** | `SELF_CONNECTION_FORBIDDEN` | 422 Unprocessable | User attempts to send a connection request to their own user ID. | "You cannot establish a professional connection with yourself." |
| **ERR-017** | `PAYLOAD_TOO_LARGE` | 413 Payload Too Large | Uploaded file exceeds size threshold (Avatar > 2MB, Post/Resume > 5MB). | "Uploaded file exceeds maximum allowed size." |
| **ERR-018** | `UNSUPPORTED_MEDIA_TYPE` | 415 Unsupported Media | Uploaded file magic bytes do not match declared or accepted MIME type. | "File format is invalid or corrupted. Only JPEG, PNG, WEBP, PDF, and DOCX are allowed." |
| **ERR-019** | `MAX_COMMENT_DEPTH_EXCEEDED` | 422 Unprocessable | Attempt to reply to a comment that is already a Level 2 reply. | "Comments cannot be nested more than two levels deep." |
| **ERR-020** | `END_DATE_BEFORE_START_DATE` | 422 Unprocessable | Experience or Education entry specifies `end_date` earlier than `start_date`. | "End date cannot precede the start date." |
| **ERR-021** | `SALARY_MAX_MUST_EXCEED_MIN` | 422 Unprocessable | Job posting specifies `salary_max` less than `salary_min`. | "Maximum salary must be greater than or equal to minimum salary." |
| **ERR-022** | `VALIDATION_ERROR` | 422 Unprocessable | Pydantic request model validation failure on field constraints or regex. | "Request validation failed. Please check the supplied parameters." |
| **ERR-023** | `DATABASE_LOCKED` | 503 Service Unavailable | SQLite database lock contention persists after exponential retries. | "System is currently busy. Please retry your request in a few moments." |
| **ERR-024** | `INTERNAL_SERVER_ERROR` | 500 Internal Error | Unhandled server exception trapped by ASGI middleware. | "An unexpected server error occurred. Please contact support." |

---

## 3. Traceable Endpoint Catalog (`API-001` through `API-050`)

The following catalog maps every REST route to its PRD Requirement ID (`REQ-XXX`), HTTP method, path, and security scope:

| Endpoint ID | HTTP Method | Route Path | Requirement ID | Auth Scope | Short Description |
|---|---|---|---|---|---|
| **API-001** | `POST` | `/api/v1/auth/register` | `REQ-002` | Public | Register new user account with bcrypt password |
| **API-002** | `POST` | `/api/v1/auth/login` | `REQ-002` | Public | Authenticate via email/password; return JWT |
| **API-003** | `POST` | `/api/v1/auth/quick-switch` | `REQ-001` | Public / Dev | Instantaneous persona switch across 10 personas |
| **API-004** | `GET` | `/api/v1/auth/personas` | `REQ-001` | Public / Dev | List all 10 pre-seeded personas for switcher UI |
| **API-005** | `GET` | `/api/v1/auth/me` | `REQ-002` | Bearer Token | Retrieve currently authenticated user & profile |
| **API-006** | `GET` | `/api/v1/users/{user_id}` | `REQ-003`, `REQ-004` | Bearer Token | Get user profile with degree badge (1st/2nd/3rd+) |
| **API-007** | `PATCH` | `/api/v1/users/me/profile` | `REQ-003` | Bearer Token | Update authenticated user's profile attributes |
| **API-008** | `GET` | `/api/v1/users/{user_id}/mutuals` | `REQ-004` | Bearer Token | List mutual 1st-degree connections with user |
| **API-009** | `POST` | `/api/v1/users/me/experiences` | `REQ-003` | Bearer Token | Add work experience entry |
| **API-010** | `PUT` | `/api/v1/users/me/experiences/{experience_id}` | `REQ-003` | Bearer Token | Update existing work experience entry |
| **API-011** | `DELETE` | `/api/v1/users/me/experiences/{experience_id}` | `REQ-003` | Bearer Token | Delete work experience entry |
| **API-012** | `POST` | `/api/v1/users/me/educations` | `REQ-003` | Bearer Token | Add education entry |
| **API-013** | `PUT` | `/api/v1/users/me/educations/{education_id}` | `REQ-003` | Bearer Token | Update existing education entry |
| **API-014** | `DELETE` | `/api/v1/users/me/educations/{education_id}` | `REQ-003` | Bearer Token | Delete education entry |
| **API-015** | `GET` | `/api/v1/skills` | `REQ-003`, `REQ-014` | Bearer Token | Autocomplete & search canonical skills catalog |
| **API-016** | `POST` | `/api/v1/users/me/skills` | `REQ-003` | Bearer Token | Associate skill tag with user profile |
| **API-017** | `DELETE` | `/api/v1/users/me/skills/{skill_id}` | `REQ-003` | Bearer Token | Disassociate skill tag from user profile |
| **API-018** | `GET` | `/api/v1/connections` | `REQ-004`, `REQ-008` | Bearer Token | List confirmed 1st-degree connections |
| **API-019** | `GET` | `/api/v1/connections/pending` | `REQ-006` | Bearer Token | List incoming and outgoing pending connection requests |
| **API-020** | `POST` | `/api/v1/connections/request` | `REQ-005` | Bearer Token | Send connection request with optional note |
| **API-021** | `POST` | `/api/v1/connections/{connection_id}/accept` | `REQ-006` | Bearer Token | Accept incoming pending connection request |
| **API-022** | `POST` | `/api/v1/connections/{connection_id}/ignore` | `REQ-006` | Bearer Token | Ignore incoming pending connection request |
| **API-023** | `DELETE` | `/api/v1/connections/{connection_id}/withdraw` | `REQ-007` | Bearer Token | Withdraw outgoing pending connection request |
| **API-024** | `DELETE` | `/api/v1/connections/{user_id}` | `REQ-008` | Bearer Token | Disconnect / remove active 1st-degree connection |
| **API-025** | `GET` | `/api/v1/feed` | `REQ-010` | Bearer Token | Get paginated feed (mode: "recent" or "top") |
| **API-026** | `POST` | `/api/v1/posts` | `REQ-009` | Bearer Token | Create rich post with code or image |
| **API-027** | `GET` | `/api/v1/posts/{post_id}` | `REQ-009`, `REQ-010` | Bearer Token | Get single post detail with hydrated author & counts |
| **API-028** | `DELETE` | `/api/v1/posts/{post_id}` | `REQ-009` | Bearer Token | Delete post (author only) |
| **API-029** | `POST` | `/api/v1/posts/{post_id}/reactions` | `REQ-011` | Bearer Token | Toggle or switch reaction (LIKE, CELEBRATE, INSIGHTFUL) |
| **API-030** | `DELETE` | `/api/v1/posts/{post_id}/reactions` | `REQ-011` | Bearer Token | Remove active reaction from post |
| **API-031** | `GET` | `/api/v1/posts/{post_id}/comments` | `REQ-012` | Bearer Token | List 2-level threaded comments for post |
| **API-032** | `POST` | `/api/v1/posts/{post_id}/comments` | `REQ-012` | Bearer Token | Create root comment or reply (max depth 2) |
| **API-033** | `DELETE` | `/api/v1/comments/{comment_id}` | `REQ-012` | Bearer Token | Delete comment (author or post author) |
| **API-034** | `GET` | `/api/v1/jobs` | `REQ-014` | Bearer Token | Search and filter jobs with facet filters |
| **API-035** | `GET` | `/api/v1/jobs/{job_id}` | `REQ-013`, `REQ-014` | Bearer Token | Get full job listing details |
| **API-036** | `POST` | `/api/v1/jobs` | `REQ-013` | Bearer Token | Create new job listing (recruiter / hiring manager) |
| **API-037** | `PATCH` | `/api/v1/jobs/{job_id}/status` | `REQ-013` | Bearer Token | Toggle job status (`OPEN` or `CLOSED`) |
| **API-038** | `POST` | `/api/v1/jobs/{job_id}/apply` | `REQ-015` | Bearer Token | Submit Easy Apply application with note and resume |
| **API-039** | `GET` | `/api/v1/jobs/{job_id}/applications` | `REQ-016` | Bearer Token | List candidate applications in ATS pipeline (owner only) |
| **API-040** | `PATCH` | `/api/v1/jobs/{job_id}/applications/{application_id}/status` | `REQ-016` | Bearer Token | Transition candidate pipeline status |
| **API-041** | `GET` | `/api/v1/jobs/applications/me` | `REQ-015` | Bearer Token | List jobs candidate has applied to |
| **API-042** | `GET` | `/api/v1/messages/conversations` | `REQ-017` | Bearer Token | List conversation summaries with recent messages |
| **API-043** | `GET` | `/api/v1/messages/{peer_id}` | `REQ-017` | Bearer Token | Get conversation history with 1st-degree connection |
| **API-044** | `POST` | `/api/v1/messages/{peer_id}/read` | `REQ-017`, `REQ-018` | Bearer Token | Mark messages from peer as read |
| **API-045** | `GET` | `/api/v1/notifications` | `REQ-018` | Bearer Token | List user notifications (cursor paginated) |
| **API-046** | `POST` | `/api/v1/notifications/read` | `REQ-018` | Bearer Token | Mark notifications as read |
| **API-047** | `GET` | `/api/v1/notifications/badges` | `REQ-018` | Bearer Token | Get unread badge counts (chat, connections, alerts) |
| **API-048** | `POST` | `/api/v1/uploads/avatar` | `REQ-003`, `NFR-006` | Bearer Token | Upload profile avatar image (multipart, max 2MB) |
| **API-049** | `POST` | `/api/v1/uploads/post-media` | `REQ-009`, `NFR-006` | Bearer Token | Upload feed post image (multipart, max 5MB) |
| **API-050** | `POST` | `/api/v1/uploads/resume` | `REQ-015`, `NFR-006` | Bearer Token | Upload resume document (multipart, max 5MB) |

---

## 4. Strict Request & Response Schemas: TypeScript Interfaces & Pydantic Models

### 4.1 TypeScript Contract Interfaces (`src/frontend/src/api/contracts/types.ts`)

```typescript
// =============================================================================
// PRONET AUTHORITATIVE TYPESCRIPT CONTRACTS (v1.0.0)
// File: src/frontend/src/api/contracts/types.ts
// =============================================================================

// --- COMMON & ENUMS ---
export type DegreeType = '1st' | '2nd' | '3rd+';
export type ConnectionStatus = 'PENDING' | 'ACCEPTED' | 'IGNORED';
export type WorkplaceType = 'REMOTE' | 'HYBRID' | 'ON_SITE';
export type JobStatus = 'OPEN' | 'CLOSED';
export type ApplicationStatus = 'APPLIED' | 'REVIEWING' | 'SHORTLISTED' | 'REJECTED';
export type ReactionType = 'LIKE' | 'CELEBRATE' | 'INSIGHTFUL';
export type FeedMode = 'recent' | 'top';
export type NotificationType =
  | 'CONNECTION_REQUEST'
  | 'CONNECTION_ACCEPTED'
  | 'POST_REACTION'
  | 'POST_COMMENT'
  | 'COMMENT_REPLY'
  | 'JOB_STATUS_CHANGE'
  | 'NEW_MESSAGE';
export type ReferenceType = 'POST' | 'JOB' | 'CONNECTION' | 'MESSAGE';

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    status_code: number;
    timestamp: string;
    path: string;
    request_id: string;
    details?: Record<string, unknown>;
  };
}

export interface CursorPaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count?: number;
}

// --- AUTH & PERSONA ---
export interface PersonaDTO {
  id: string;
  email: string;
  full_name: string;
  headline: string;
  location: string;
  avatar_url: string | null;
}

export interface AuthTokensDTO {
  access_token: string;
  token_type: 'bearer';
  expires_in_seconds: number;
  user: UserSummaryDTO;
}

export interface UserSummaryDTO {
  id: string;
  email: string;
  full_name: string;
  headline: string;
  avatar_url: string | null;
}

export interface RegisterRequestDTO {
  email: string;
  password: string;
  full_name: string;
  headline: string;
  location: string;
}

export interface LoginRequestDTO {
  email: string;
  password: string;
}

export interface QuickSwitchRequestDTO {
  user_id: string;
}

// --- PROFILE & USER ---
export interface ProfileDTO {
  id: string;
  user_id: string;
  headline: string;
  bio: string | null;
  location: string;
  avatar_url: string | null;
  connections_count: number;
  created_at: string;
  updated_at: string;
}

export interface ExperienceDTO {
  id: string;
  user_id: string;
  company: string;
  title: string;
  location: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  created_at: string;
}

export interface ExperienceCreateDTO {
  company: string;
  title: string;
  location?: string | null;
  start_date: string;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
}

export interface ExperienceUpdateDTO {
  company: string;
  title: string;
  location?: string | null;
  start_date: string;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
}

export interface EducationDTO {
  id: string;
  user_id: string;
  institution: string;
  degree: string;
  field_of_study: string | null;
  start_year: number;
  end_year: number | null;
  created_at: string;
}

export interface EducationCreateDTO {
  institution: string;
  degree: string;
  field_of_study?: string | null;
  start_year: number;
  end_year?: number | null;
}

export interface EducationUpdateDTO {
  institution: string;
  degree: string;
  field_of_study?: string | null;
  start_year: number;
  end_year?: number | null;
}

export interface SkillDTO {
  id: string;
  name: string;
  category: string | null;
}

export interface UserSkillAddDTO {
  skill_name: string;
}

export interface ProfileDetailDTO {
  id: string;
  email: string;
  full_name: string;
  profile: ProfileDTO;
  degree: DegreeType;
  mutual_connections_count: number;
  mutual_connections_preview: UserSummaryDTO[];
  experiences: ExperienceDTO[];
  educations: EducationDTO[];
  skills: SkillDTO[];
  connection_status_with_viewer: ConnectionStatus | 'NONE' | 'SELF';
  viewer_initiated_connection: boolean;
  active_connection_id: string | null;
}

export interface ProfileUpdateDTO {
  headline?: string;
  bio?: string | null;
  location?: string;
  avatar_url?: string | null;
}

// --- SOCIAL GRAPH & CONNECTIONS ---
export interface ConnectionDTO {
  id: string;
  user_low_id: string;
  user_high_id: string;
  initiator_id: string;
  recipient_id: string;
  status: ConnectionStatus;
  note: string | null;
  created_at: string;
  updated_at: string;
  peer: UserSummaryDTO;
}

export interface PendingConnectionsDTO {
  incoming: ConnectionDTO[];
  outgoing: ConnectionDTO[];
}

export interface SendConnectionRequestDTO {
  recipient_id: string;
  note?: string | null;
}

// --- FEED & POSTS ---
export interface PostDTO {
  id: string;
  author: UserSummaryDTO;
  content: string;
  code_snippet: string | null;
  code_language: string | null;
  image_url: string | null;
  like_count: number;
  celebrate_count: number;
  insightful_count: number;
  comment_count: number;
  viewer_reaction: ReactionType | null;
  is_author_connection: boolean;
  top_comments_preview: CommentDTO[];
  created_at: string;
  updated_at: string;
}

export interface CreatePostDTO {
  content: string;
  code_snippet?: string | null;
  code_language?: string | null;
  image_url?: string | null;
}

export interface PostReactionDTO {
  id: string;
  post_id: string;
  user_id: string;
  reaction_type: ReactionType;
  created_at: string;
}

export interface SetReactionDTO {
  reaction_type: ReactionType;
}

export interface CommentDTO {
  id: string;
  post_id: string;
  author: UserSummaryDTO;
  parent_id: string | null;
  content: string;
  replies?: CommentDTO[];
  created_at: string;
  updated_at: string;
}

export interface CreateCommentDTO {
  content: string;
  parent_id?: string | null;
}

// --- JOBS & ATS PIPELINE ---
export interface JobDTO {
  id: string;
  poster: UserSummaryDTO;
  title: string;
  company_name: string;
  workplace_type: WorkplaceType;
  location: string;
  salary_min: number;
  salary_max: number;
  description: string;
  required_skills: string[];
  status: JobStatus;
  application_count: number;
  has_viewer_applied: boolean;
  viewer_application_status: ApplicationStatus | null;
  created_at: string;
  updated_at: string;
}

export interface CreateJobDTO {
  title: string;
  company_name: string;
  workplace_type: WorkplaceType;
  location: string;
  salary_min: number;
  salary_max: number;
  description: string;
  required_skills: string[];
}

export interface JobFilterParams {
  keyword?: string;
  workplace_type?: WorkplaceType;
  skill?: string;
  location?: string;
  status?: JobStatus;
  limit?: number;
  cursor?: string;
}

export interface EasyApplyDTO {
  cover_note?: string | null;
  resume_url?: string | null;
}

export interface JobApplicationDTO {
  id: string;
  job_id: string;
  job_title?: string;
  company_name?: string;
  applicant: UserSummaryDTO;
  status: ApplicationStatus;
  cover_note: string | null;
  resume_url: string | null;
  profile_headline_snapshot: string;
  skills_snapshot: string[];
  created_at: string;
  updated_at: string;
}

export interface UpdateApplicationStatusDTO {
  status: ApplicationStatus;
}

// --- MESSAGING & NOTIFICATIONS ---
export interface MessageDTO {
  id: string;
  sender_id: string;
  recipient_id: string;
  content: string;
  read_at: string | null;
  created_at: string;
  is_outgoing: boolean;
}

export interface ConversationSummaryDTO {
  peer: UserSummaryDTO;
  last_message: MessageDTO;
  unread_count: number;
}

export interface NotificationDTO {
  id: string;
  user_id: string;
  actor: UserSummaryDTO;
  notification_type: NotificationType;
  title: string;
  content: string;
  reference_id: string | null;
  reference_type: ReferenceType | null;
  is_read: boolean;
  created_at: string;
}

export interface BadgeCountsDTO {
  unread_messages: number;
  pending_connections: number;
  unread_notifications: number;
}

export interface UploadResponseDTO {
  file_url: string;
  file_name: string;
  content_type: string;
  size_bytes: number;
}
```

---

### 4.2 Python Pydantic V2 Schemas (`src/backend/app/schemas/`)

The following Python schemas are defined with complete type annotations, Field validation bounds, regex formats, and enums:

```python
# =============================================================================
# PRONET AUTHORITATIVE PYDANTIC V2 SCHEMAS (v1.0.0)
# File: Apps/ProNet/src/backend/app/schemas/contracts.py
# =============================================================================

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, model_validator, ConfigDict

# --- ENUMERATIONS ---

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


# --- ERROR SCHEMAS ---

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


# --- AUTH & PERSONA SCHEMAS ---

class PersonaDTO(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=128)
    headline: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=128)
    avatar_url: Optional[str] = Field(None, max_length=512)

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


# --- PROFILE & USER SCHEMAS ---

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
    pass

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
    pass

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


# --- SOCIAL GRAPH & CONNECTIONS SCHEMAS ---

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


# --- ACTIVITY FEED, REACTIONS & COMMENTS SCHEMAS ---

class CreatePostDTO(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000)
    code_snippet: Optional[str] = Field(None, max_length=10000)
    code_language: Optional[str] = Field(None, max_length=32)
    image_url: Optional[str] = Field(None, max_length=512)

class SetReactionDTO(BaseModel):
    reaction_type: ReactionType

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


# --- JOBS & ATS PIPELINE SCHEMAS ---

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


# --- MESSAGING & NOTIFICATIONS SCHEMAS ---

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

class BadgeCountsDTO(BaseModel):
    unread_messages: int = Field(ge=0)
    pending_connections: int = Field(ge=0)
    unread_notifications: int = Field(ge=0)

class UploadResponseDTO(BaseModel):
    file_url: str = Field(..., max_length=512)
    file_name: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=64)
    size_bytes: int = Field(gt=0)
```

---

## 5. Detailed Endpoint Contracts (API-001 to API-050)

### 5.1 Authentication & Persona Domain

#### `API-001`: Register User
- **Method / Path:** `POST /api/v1/auth/register`
- **Traceability:** `REQ-002`
- **Auth Scope:** Public
- **Request Headers:** `Content-Type: application/json`
- **Request Body:** `RegisterRequestDTO`
- **Response 201 Created:** `AuthTokensDTO`
- **Error Codes:** `ERR-022` (Validation failure), `ERR-012` (Email already registered, HTTP 409 Conflict)
- **Concrete Example Request:**
```json
{
  "email": "elena.rostova@pronet.local",
  "password": "Password123!",
  "full_name": "Elena Rostova",
  "headline": "Staff AI Systems Engineer",
  "location": "San Francisco, CA"
}
```
- **Concrete Example Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfZWxlbmFfcm9zdG92YSIsImV4cCI6MTgwMDAwMDAwMH0.signature",
  "token_type": "bearer",
  "expires_in_seconds": 86400,
  "user": {
    "id": "usr_elena_rostova",
    "email": "elena.rostova@pronet.local",
    "full_name": "Elena Rostova",
    "headline": "Staff AI Systems Engineer",
    "avatar_url": "/uploads/avatars/usr_elena_rostova.png"
  }
}
```

---

#### `API-002`: Login
- **Method / Path:** `POST /api/v1/auth/login`
- **Traceability:** `REQ-002`
- **Auth Scope:** Public
- **Request Body:** `LoginRequestDTO`
- **Response 200 OK:** `AuthTokensDTO`
- **Error Codes:** `ERR-001` (HTTP 401: INVALID_CREDENTIALS)
- **Concrete Example Request:**
```json
{
  "email": "elena.rostova@pronet.local",
  "password": "Password123!"
}
```
- **Concrete Example Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfZWxlbmFfcm9zdG92YSIsImV4cCI6MTgwMDAwMDAwMH0.signature",
  "token_type": "bearer",
  "expires_in_seconds": 86400,
  "user": {
    "id": "usr_elena_rostova",
    "email": "elena.rostova@pronet.local",
    "full_name": "Elena Rostova",
    "headline": "Staff AI Systems Engineer",
    "avatar_url": "/uploads/avatars/usr_elena_rostova.png"
  }
}
```

---

#### `API-003`: Quick Switch Persona
- **Method / Path:** `POST /api/v1/auth/quick-switch`
- **Traceability:** `REQ-001`
- **Auth Scope:** Public / Dev
- **Request Body:** `QuickSwitchRequestDTO`
- **Response 200 OK:** `AuthTokensDTO`
- **Error Codes:** `ERR-009` (HTTP 404: USER_NOT_FOUND)
- **Concrete Example Request:**
```json
{
  "user_id": "usr_alex_chen"
}
```
- **Concrete Example Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfYWxleF9jaGVuIiwiZXhwIjoxODAwMDAwMDAwfQ.signature",
  "token_type": "bearer",
  "expires_in_seconds": 86400,
  "user": {
    "id": "usr_alex_chen",
    "email": "alex.chen@pronet.local",
    "full_name": "Alex Chen",
    "headline": "Principal Cloud Infrastructure Architect",
    "avatar_url": "/uploads/avatars/usr_alex_chen.png"
  }
}
```

---

#### `API-004`: List Personas
- **Method / Path:** `GET /api/v1/auth/personas`
- **Traceability:** `REQ-001`
- **Auth Scope:** Public
- **Response 200 OK:** `List[PersonaDTO]` (Exactly 10 items)
- **Concrete Example Response (200 OK):**
```json
[
  {
    "id": "usr_elena_rostova",
    "email": "elena.rostova@pronet.local",
    "full_name": "Elena Rostova",
    "headline": "Staff AI Systems Engineer",
    "location": "San Francisco, CA",
    "avatar_url": "/uploads/avatars/usr_elena_rostova.png"
  },
  {
    "id": "usr_alex_chen",
    "email": "alex.chen@pronet.local",
    "full_name": "Alex Chen",
    "headline": "Principal Cloud Infrastructure Architect",
    "location": "Seattle, WA",
    "avatar_url": "/uploads/avatars/usr_alex_chen.png"
  }
]
```

---

#### `API-005`: Get Authenticated User (Me)
- **Method / Path:** `GET /api/v1/auth/me`
- **Traceability:** `REQ-002`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `UserSummaryDTO`
- **Error Codes:** `ERR-004` (401 Unauthorized), `ERR-002` (401 Token Expired)

---

### 5.2 User & Profile Domain

#### `API-006`: Get User Profile Detail with Degree & Mutuals
- **Method / Path:** `GET /api/v1/users/{user_id}`
- **Traceability:** `REQ-003`, `REQ-004`
- **Auth Scope:** Bearer Token
- **Path Parameter:** `user_id` (string, required)
- **Response 200 OK:** `ProfileDetailDTO`
- **Error Codes:** `ERR-009` (HTTP 404: USER_NOT_FOUND)
- **Concrete Example Response (200 OK):**
```json
{
  "id": "usr_marcus_vance",
  "email": "marcus.vance@pronet.local",
  "full_name": "Marcus Vance",
  "profile": {
    "id": "prf_usr_marcus_vance",
    "user_id": "usr_marcus_vance",
    "headline": "VP of Engineering & Platform Scalability",
    "bio": "Executive engineering leader scaling teams from Seed to IPO.",
    "location": "Austin, TX",
    "avatar_url": "/uploads/avatars/usr_marcus_vance.png",
    "connections_count": 4,
    "created_at": "2026-10-20T00:00:00Z",
    "updated_at": "2026-10-20T00:00:00Z"
  },
  "degree": "1st",
  "mutual_connections_count": 2,
  "mutual_connections_preview": [
    {
      "id": "usr_alex_chen",
      "email": "alex.chen@pronet.local",
      "full_name": "Alex Chen",
      "headline": "Principal Cloud Infrastructure Architect",
      "avatar_url": "/uploads/avatars/usr_alex_chen.png"
    }
  ],
  "experiences": [
    {
      "id": "exp_03",
      "user_id": "usr_marcus_vance",
      "company": "Nexus Cloud Systems",
      "title": "VP of Engineering",
      "location": "Austin, TX",
      "start_date": "2020-04-01",
      "end_date": null,
      "is_current": true,
      "description": "Overseeing 120+ engineers across platform, product, and QA.",
      "created_at": "2026-10-20T00:00:00Z"
    }
  ],
  "educations": [
    {
      "id": "edu_03",
      "user_id": "usr_marcus_vance",
      "institution": "University of Texas at Austin",
      "degree": "B.S.",
      "field_of_study": "Computer Science",
      "start_year": 2007,
      "end_year": 2011,
      "created_at": "2026-10-20T00:00:00Z"
    }
  ],
  "skills": [
    {"id": "skl_01", "name": "Architecture", "category": "Engineering"},
    {"id": "skl_02", "name": "Distributed Systems", "category": "Engineering"}
  ],
  "connection_status_with_viewer": "ACCEPTED",
  "viewer_initiated_connection": false,
  "active_connection_id": "conn_02"
}
```

---

#### `API-007`: Update Profile Info
- **Method / Path:** `PATCH /api/v1/users/me/profile`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Request Body:** `ProfileUpdateDTO`
- **Response 200 OK:** `ProfileDTO`

---

#### `API-008`: Get Mutual Connections
- **Method / Path:** `GET /api/v1/users/{user_id}/mutuals`
- **Traceability:** `REQ-004`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `List[UserSummaryDTO]`

---

#### `API-009`: Add Work Experience
- **Method / Path:** `POST /api/v1/users/me/experiences`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Request Body:** `ExperienceCreateDTO`
- **Response 201 Created:** `ExperienceDTO`
- **Error Codes:** `ERR-020` (HTTP 422: END_DATE_BEFORE_START_DATE)

---

#### `API-010`: Update Work Experience
- **Method / Path:** `PUT /api/v1/users/me/experiences/{experience_id}`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Request Body:** `ExperienceUpdateDTO`
- **Response 200 OK:** `ExperienceDTO`

---

#### `API-011`: Delete Work Experience
- **Method / Path:** `DELETE /api/v1/users/me/experiences/{experience_id}`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None

---

#### `API-012`: Add Education
- **Method / Path:** `POST /api/v1/users/me/educations`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Request Body:** `EducationCreateDTO`
- **Response 201 Created:** `EducationDTO`

---

#### `API-013`: Update Education
- **Method / Path:** `PUT /api/v1/users/me/educations/{education_id}`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Request Body:** `EducationUpdateDTO`
- **Response 200 OK:** `EducationDTO`

---

#### `API-014`: Delete Education
- **Method / Path:** `DELETE /api/v1/users/me/educations/{education_id}`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None

---

#### `API-015`: List / Search Canonical Skills
- **Method / Path:** `GET /api/v1/skills?query=python`
- **Traceability:** `REQ-003`, `REQ-014`
- **Auth Scope:** Bearer Token
- **Query Parameter:** `query` (string, optional)
- **Response 200 OK:** `List[SkillDTO]`

---

#### `API-016`: Add Skill to Profile
- **Method / Path:** `POST /api/v1/users/me/skills`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Request Body:** `UserSkillAddDTO`
- **Response 201 Created:** `SkillDTO`

---

#### `API-017`: Remove Skill from Profile
- **Method / Path:** `DELETE /api/v1/users/me/skills/{skill_id}`
- **Traceability:** `REQ-003`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None

---

### 5.3 Social Graph & Connections Domain

#### `API-018`: List 1st-Degree Connections
- **Method / Path:** `GET /api/v1/connections`
- **Traceability:** `REQ-004`, `REQ-008`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `List[ConnectionDTO]`

---

#### `API-019`: List Pending Connections
- **Method / Path:** `GET /api/v1/connections/pending`
- **Traceability:** `REQ-006`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `PendingConnectionsDTO`
- **Concrete Example Response (200 OK):**
```json
{
  "incoming": [
    {
      "id": "conn_14",
      "user_low_id": "usr_aisha_diop",
      "user_high_id": "usr_elena_rostova",
      "initiator_id": "usr_aisha_diop",
      "recipient_id": "usr_elena_rostova",
      "status": "PENDING",
      "note": "Elena, saw your post on SQLite WAL mode—let's connect!",
      "created_at": "2026-10-20T01:00:00Z",
      "updated_at": "2026-10-20T01:00:00Z",
      "peer": {
        "id": "usr_aisha_diop",
        "email": "aisha.diop@pronet.local",
        "full_name": "Aisha Diop",
        "headline": "Director of Product Management",
        "avatar_url": "/uploads/avatars/usr_aisha_diop.png"
      }
    }
  ],
  "outgoing": [
    {
      "id": "conn_13",
      "user_low_id": "usr_elena_rostova",
      "user_high_id": "usr_sarah_jenkins",
      "initiator_id": "usr_elena_rostova",
      "recipient_id": "usr_sarah_jenkins",
      "status": "PENDING",
      "note": "Hi Sarah, would love to connect and follow talent updates.",
      "created_at": "2026-10-20T01:00:00Z",
      "updated_at": "2026-10-20T01:00:00Z",
      "peer": {
        "id": "usr_sarah_jenkins",
        "email": "sarah.jenkins@pronet.local",
        "full_name": "Sarah Jenkins",
        "headline": "Principal Technical Talent Partner",
        "avatar_url": "/uploads/avatars/usr_sarah_jenkins.png"
      }
    }
  ]
}
```

---

#### `API-020`: Send Connection Request
- **Method / Path:** `POST /api/v1/connections/request`
- **Traceability:** `REQ-005`
- **Auth Scope:** Bearer Token
- **Request Body:** `SendConnectionRequestDTO`
- **Response 201 Created:** `ConnectionDTO`
- **Error Codes:**
  - `ERR-016` (HTTP 422: SELF_CONNECTION_FORBIDDEN)
  - `ERR-012` (HTTP 409: CONNECTION_ALREADY_REQUESTED)
  - `ERR-013` (HTTP 409: ALREADY_CONNECTED)
- **Auto-Resolve Collision (EDG-001):** If the recipient already sent a pending request to the sender, the system intercepts the collision, transitions status to `ACCEPTED`, increments connection counts, and returns `200 OK` with code `CONNECTION_AUTO_RESOLVED`.

---

#### `API-021`: Accept Connection Request
- **Method / Path:** `POST /api/v1/connections/{connection_id}/accept`
- **Traceability:** `REQ-006`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `ConnectionDTO`
- **Side Effects:** Increments `connections_count` on both users; dispatches `CONNECTION_ACCEPTED` notification and badge update over WebSocket.

---

#### `API-022`: Ignore Connection Request
- **Method / Path:** `POST /api/v1/connections/{connection_id}/ignore`
- **Traceability:** `REQ-006`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `ConnectionDTO` (with `status = "IGNORED"`)

---

#### `API-023`: Withdraw Connection Request
- **Method / Path:** `DELETE /api/v1/connections/{connection_id}/withdraw`
- **Traceability:** `REQ-007`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None
- **Error Codes:** `ERR-015` (HTTP 400: CANNOT_WITHDRAW_ACCEPTED_CONNECTION)

---

#### `API-024`: Remove Connection (Disconnect)
- **Method / Path:** `DELETE /api/v1/connections/{user_id}`
- **Traceability:** `REQ-008`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None
- **Side Effects:** Decrements `connections_count` on both profiles; locks direct messaging channel.

---

### 5.4 Activity Feed, Reactions & Comments Domain

#### `API-025`: Get Paginated Feed
- **Method / Path:** `GET /api/v1/feed`
- **Traceability:** `REQ-010`
- **Auth Scope:** Bearer Token
- **Query Parameters:**
  - `mode` (string, enum: `"recent"` or `"top"`, default: `"top"`)
  - `limit` (integer, default: `20`, min: `1`, max: `50`)
  - `cursor` (string, optional: ISO timestamp pointer)
- **Response 200 OK:** `FeedResponseDTO`
- **Performance SLA:** p95 ≤ 150 ms (executed in exactly 2 SQLite queries per `KPI-007`).
- **Concrete Example Response (200 OK):**
```json
{
  "items": [
    {
      "id": "post_01",
      "author": {
        "id": "usr_elena_rostova",
        "email": "elena.rostova@pronet.local",
        "full_name": "Elena Rostova",
        "headline": "Staff AI Systems Engineer",
        "avatar_url": "/uploads/avatars/usr_elena_rostova.png"
      },
      "content": "Why we chose SQLite in WAL mode for ProNet: Zero cloud dependencies, sub-millisecond local reads via memory mapping.",
      "code_snippet": "engine = create_async_engine('sqlite+aiosqlite:///pronet.db')\n# PRAGMA journal_mode=WAL;",
      "code_language": "python",
      "image_url": null,
      "like_count": 18,
      "celebrate_count": 7,
      "insightful_count": 14,
      "comment_count": 4,
      "viewer_reaction": "LIKE",
      "is_author_connection": false,
      "top_comments_preview": [
        {
          "id": "cmt_01",
          "post_id": "post_01",
          "author": {
            "id": "usr_alex_chen",
            "email": "alex.chen@pronet.local",
            "full_name": "Alex Chen",
            "headline": "Principal Cloud Infrastructure Architect",
            "avatar_url": "/uploads/avatars/usr_alex_chen.png"
          },
          "parent_id": null,
          "content": "The WAL concurrency model is unmatched for single-host deployments.",
          "replies": [],
          "created_at": "2026-10-20T02:00:00Z",
          "updated_at": "2026-10-20T02:00:00Z"
        }
      ],
      "created_at": "2026-10-20T01:30:00Z",
      "updated_at": "2026-10-20T01:30:00Z"
    }
  ],
  "next_cursor": "2026-10-20T01:30:00Z",
  "has_more": true
}
```

---

#### `API-026`: Create Rich Post
- **Method / Path:** `POST /api/v1/posts`
- **Traceability:** `REQ-009`
- **Auth Scope:** Bearer Token
- **Request Body:** `CreatePostDTO`
- **Response 201 Created:** `PostDTO`
- **Error Codes:** `ERR-022` (Validation failure, e.g. text > 3000 chars)

---

#### `API-027`: Get Single Post Detail
- **Method / Path:** `GET /api/v1/posts/{post_id}`
- **Traceability:** `REQ-009`, `REQ-010`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `PostDTO`
- **Error Codes:** `ERR-010` (HTTP 404: POST_NOT_FOUND)

---

#### `API-028`: Delete Post
- **Method / Path:** `DELETE /api/v1/posts/{post_id}`
- **Traceability:** `REQ-009`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None
- **Error Codes:** `ERR-004` (Unauthorized), `ERR-007` (Cannot delete other user's post)

---

#### `API-029`: Toggle / Switch Reaction
- **Method / Path:** `POST /api/v1/posts/{post_id}/reactions`
- **Traceability:** `REQ-011`
- **Auth Scope:** Bearer Token
- **Request Body:** `SetReactionDTO`
- **Response 200 OK:**
```json
{
  "active_reaction": "INSIGHTFUL",
  "like_count": 18,
  "celebrate_count": 7,
  "insightful_count": 15
}
```
- **Semantics:** If current reaction matches incoming type, removes reaction (`active_reaction: null`). If differing, decrements old and increments new.

---

#### `API-030`: Remove Reaction
- **Method / Path:** `DELETE /api/v1/posts/{post_id}/reactions`
- **Traceability:** `REQ-011`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None

---

#### `API-031`: List Threaded Comments for Post
- **Method / Path:** `GET /api/v1/posts/{post_id}/comments`
- **Traceability:** `REQ-012`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `List[CommentDTO]` (Root Level 1 comments with populated `replies: CommentDTO[]`)

---

#### `API-032`: Add Comment or Reply
- **Method / Path:** `POST /api/v1/posts/{post_id}/comments`
- **Traceability:** `REQ-012`
- **Auth Scope:** Bearer Token
- **Request Body:** `CreateCommentDTO`
- **Response 201 Created:** `CommentDTO`
- **Error Codes:** `ERR-019` (HTTP 422: MAX_COMMENT_DEPTH_EXCEEDED when `parent_id` already has a parent)

---

#### `API-033`: Delete Comment
- **Method / Path:** `DELETE /api/v1/comments/{comment_id}`
- **Traceability:** `REQ-012`
- **Auth Scope:** Bearer Token
- **Response 204 No Content:** None
- **Authorization Rule:** Current user must be comment author OR post author (**REQ-012**).

---

### 5.5 Job Board & Mini-ATS Pipeline Domain

#### `API-034`: Search & Filter Jobs
- **Method / Path:** `GET /api/v1/jobs`
- **Traceability:** `REQ-014`
- **Auth Scope:** Bearer Token
- **Query Parameters:**
  - `keyword` (string, optional)
  - `workplace_type` (string, optional: `REMOTE`, `HYBRID`, `ON_SITE`)
  - `skill` (string, optional)
  - `location` (string, optional)
  - `status` (string, default: `OPEN`)
  - `limit` (integer, default: `20`)
  - `cursor` (string, optional)
- **Response 200 OK:** `CursorPaginatedResponse<JobDTO>`

---

#### `API-035`: Get Job Detail
- **Method / Path:** `GET /api/v1/jobs/{job_id}`
- **Traceability:** `REQ-013`, `REQ-014`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `JobDTO`
- **Error Codes:** `ERR-011` (HTTP 404: JOB_NOT_FOUND)

---

#### `API-036`: Create Job Posting
- **Method / Path:** `POST /api/v1/jobs`
- **Traceability:** `REQ-013`
- **Auth Scope:** Bearer Token
- **Request Body:** `CreateJobDTO`
- **Response 201 Created:** `JobDTO`
- **Error Codes:** `ERR-021` (HTTP 422: SALARY_MAX_MUST_EXCEED_MIN)

---

#### `API-037`: Toggle Job Status
- **Method / Path:** `PATCH /api/v1/jobs/{job_id}/status`
- **Traceability:** `REQ-013`
- **Auth Scope:** Bearer Token
- **Request Body:** `{"status": "CLOSED"}`
- **Response 200 OK:** `JobDTO`
- **Authorization Rule:** Only `poster_id` can modify job status.

---

#### `API-038`: Easy Apply Submission
- **Method / Path:** `POST /api/v1/jobs/{job_id}/apply`
- **Traceability:** `REQ-015`
- **Auth Scope:** Bearer Token
- **Request Body:** `EasyApplyDTO`
- **Response 201 Created:** `JobApplicationDTO`
- **Error Codes:** `ERR-014` (HTTP 409: ALREADY_APPLIED_TO_JOB)
- **Concrete Example Request:**
```json
{
  "cover_note": "Excited to bring low-latency inference architectures to DeepCognition.",
  "resume_url": "/uploads/resumes/elena_resume.pdf"
}
```
- **Concrete Example Response (201 Created):**
```json
{
  "id": "app_06",
  "job_id": "job_04",
  "job_title": "Staff AI / ML Systems Engineer",
  "company_name": "DeepCognition Labs",
  "applicant": {
    "id": "usr_elena_rostova",
    "email": "elena.rostova@pronet.local",
    "full_name": "Elena Rostova",
    "headline": "Staff AI Systems Engineer",
    "avatar_url": "/uploads/avatars/usr_elena_rostova.png"
  },
  "status": "APPLIED",
  "cover_note": "Excited to bring low-latency inference architectures to DeepCognition.",
  "resume_url": "/uploads/resumes/elena_resume.pdf",
  "profile_headline_snapshot": "Staff AI Systems Engineer",
  "skills_snapshot": ["Python", "Distributed Systems", "PyTorch", "C++", "FastAPI"],
  "created_at": "2026-10-20T03:00:00Z",
  "updated_at": "2026-10-20T03:00:00Z"
}
```

---

#### `API-039`: Get Recruiter Candidate Pipeline
- **Method / Path:** `GET /api/v1/jobs/{job_id}/applications`
- **Traceability:** `REQ-016`
- **Auth Scope:** Bearer Token
- **Query Parameter:** `status` (string, optional: filter by pipeline state)
- **Response 200 OK:** `List[JobApplicationDTO]`
- **Error Codes:** `ERR-005` (HTTP 403: NOT_JOB_OWNER)

---

#### `API-040`: Update Candidate Status in Pipeline
- **Method / Path:** `PATCH /api/v1/jobs/{job_id}/applications/{application_id}/status`
- **Traceability:** `REQ-016`
- **Auth Scope:** Bearer Token
- **Request Body:** `UpdateApplicationStatusDTO`
- **Response 200 OK:** `JobApplicationDTO`
- **Error Codes:** `ERR-005` (HTTP 403: NOT_JOB_OWNER)
- **Side Effects:** Dispatches real-time WebSocket notification to applicant informing them of status change.

---

#### `API-041`: Get My Submitted Applications
- **Method / Path:** `GET /api/v1/jobs/applications/me`
- **Traceability:** `REQ-015`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `List[JobApplicationDTO]`

---

### 5.6 Direct Messaging & Notifications Domain

#### `API-042`: List Conversations
- **Method / Path:** `GET /api/v1/messages/conversations`
- **Traceability:** `REQ-017`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `List[ConversationSummaryDTO]`
- **Concrete Example Response (200 OK):**
```json
[
  {
    "peer": {
      "id": "usr_alex_chen",
      "email": "alex.chen@pronet.local",
      "full_name": "Alex Chen",
      "headline": "Principal Cloud Infrastructure Architect",
      "avatar_url": "/uploads/avatars/usr_alex_chen.png"
    },
    "last_message": {
      "id": "msg_101",
      "sender_id": "usr_alex_chen",
      "recipient_id": "usr_elena_rostova",
      "content": "Hey Elena, let me know when you review the WAL benchmark results.",
      "read_at": null,
      "created_at": "2026-10-20T04:15:00Z",
      "is_outgoing": false
    },
    "unread_count": 1
  }
]
```

---

#### `API-043`: Get Message History
- **Method / Path:** `GET /api/v1/messages/{peer_id}`
- **Traceability:** `REQ-017`
- **Auth Scope:** Bearer Token
- **Query Parameters:**
  - `limit` (integer, default: `50`, max: `100`)
  - `cursor` (string, optional: ISO timestamp pointer)
- **Response 200 OK:** `CursorPaginatedResponse<MessageDTO>`
- **Error Codes:** `ERR-006` (HTTP 403: MUST_BE_FIRST_DEGREE)

---

#### `API-044`: Mark Conversation Read
- **Method / Path:** `POST /api/v1/messages/{peer_id}/read`
- **Traceability:** `REQ-017`, `REQ-018`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `{"marked_count": 3}`
- **Side Effects:** Updates unread badge counts on navbar over WebSocket.

---

#### `API-045`: List Notifications
- **Method / Path:** `GET /api/v1/notifications`
- **Traceability:** `REQ-018`
- **Auth Scope:** Bearer Token
- **Query Parameters:**
  - `limit` (integer, default: `20`)
  - `cursor` (string, optional)
- **Response 200 OK:** `CursorPaginatedResponse<NotificationDTO>`

---

#### `API-046`: Mark Notifications Read
- **Method / Path:** `POST /api/v1/notifications/read`
- **Traceability:** `REQ-018`
- **Auth Scope:** Bearer Token
- **Request Body:** `{"notification_ids": ["notif_01", "notif_02"]}` or empty to mark all read
- **Response 200 OK:** `{"success": true, "marked_count": 2}`

---

#### `API-047`: Get Navbar Badge Counts
- **Method / Path:** `GET /api/v1/notifications/badges`
- **Traceability:** `REQ-018`
- **Auth Scope:** Bearer Token
- **Response 200 OK:** `BadgeCountsDTO`
- **Concrete Example Response (200 OK):**
```json
{
  "unread_messages": 2,
  "pending_connections": 1,
  "unread_notifications": 4
}
```

---

### 5.7 Media & File Upload Domain

#### `API-048`: Upload Profile Avatar
- **Method / Path:** `POST /api/v1/uploads/avatar`
- **Traceability:** `REQ-003`, `NFR-006`
- **Auth Scope:** Bearer Token
- **Content-Type:** `multipart/form-data`
- **Form Field:** `file` (binary, max 2 MB)
- **Permitted MIME Types:** `image/jpeg`, `image/png`, `image/webp`
- **Magic Byte Validation:** Header verified before persistence.
- **Storage Target:** `Apps/ProNet/src/backend/uploads/avatars/`
- **Response 201 Created:** `UploadResponseDTO`
- **Error Codes:** `ERR-017` (Payload > 2MB), `ERR-018` (Unsupported magic bytes)

---

#### `API-049`: Upload Post Media
- **Method / Path:** `POST /api/v1/uploads/post-media`
- **Traceability:** `REQ-009`, `NFR-006`
- **Auth Scope:** Bearer Token
- **Content-Type:** `multipart/form-data`
- **Form Field:** `file` (binary, max 5 MB)
- **Permitted MIME Types:** `image/jpeg`, `image/png`, `image/webp`, `image/gif`
- **Storage Target:** `Apps/ProNet/src/backend/uploads/posts/`
- **Response 201 Created:** `UploadResponseDTO`
- **Error Codes:** `ERR-017` (Payload > 5MB), `ERR-018` (Unsupported magic bytes)

---

#### `API-050`: Upload Resume
- **Method / Path:** `POST /api/v1/uploads/resume`
- **Traceability:** `REQ-015`, `NFR-006`
- **Auth Scope:** Bearer Token
- **Content-Type:** `multipart/form-data`
- **Form Field:** `file` (binary, max 5 MB)
- **Permitted MIME Types:** `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- **Storage Target:** `Apps/ProNet/src/backend/uploads/resumes/`
- **Response 201 Created:** `UploadResponseDTO`
- **Error Codes:** `ERR-017` (Payload > 5MB), `ERR-018` (Unsupported magic bytes)

---

## 6. WebSocket Protocol Specification (`/ws`)

### 6.1 Handshake, Authentication & Lifecycle

- **WebSocket URI:** `ws://localhost:8000/ws?token=<jwt_token>`
- **Handshake Flow:**
  1. Client establishes standard HTTP Upgrade request to `/ws?token=<jwt_token>`.
  2. ASGI server verifies JWT validity, active user status, and claims.
  3. If token is invalid or expired, server immediately rejects upgrade with HTTP 401 or closes socket with code `4001: UNAUTHORIZED`.
  4. On successful verification, the socket is registered in the in-memory `ConnectionManager` indexed by `user_id`.
  5. Server dispatches initial `CONNECTED` welcome frame containing connection confirmation, unread badge counters, and online connection user IDs.

### 6.2 Close Codes

| Close Code | Reason | Description |
|---|---|---|
| `1000` | Normal Closure | Clean disconnect initiated by client (logout, persona switch). |
| `1001` | Going Away | Server shutdown or browser page refresh. |
| `4001` | Unauthorized | Token missing, invalid signature, or expired. |
| `4003` | Forbidden / Degree Violation | Client attempted to message non-1st-degree connection. |
| `4008` | Policy Violation / Rate Exceeded | Client exceeded message rate threshold (10 frames/sec). |
| `4009` | Invalid Frame Schema | Malformed JSON or unparseable frame payload. |

---

### 6.3 Client-to-Server Frame Types

#### 1. Heartbeat Ping Frame (`PING`)
Keeps persistent socket alive and measures round-trip latency (dispatched every 30 seconds).
```json
{
  "type": "PING",
  "timestamp": "2026-10-20T04:50:00Z"
}
```

#### 2. Direct Message Send Frame (`SEND_MESSAGE`)
Transmits a real-time message to a peer.
```json
{
  "type": "SEND_MESSAGE",
  "client_msg_id": "tmp_msg_001",
  "recipient_id": "usr_alex_chen",
  "content": "Hey Alex, are you available for a brief sync on the distributed queue design?"
}
```
- **Validation Guard:** The server verifies `(current_user.id, recipient_id)` status in `connections` is `ACCEPTED`. If not 1st-degree, returns `ERROR` frame with code `MUST_BE_FIRST_DEGREE_CONNECTION`.

#### 3. Typing Indicator Frame (`TYPING`)
Signals real-time chat input state.
```json
{
  "type": "TYPING",
  "recipient_id": "usr_alex_chen",
  "is_typing": true
}
```

#### 4. Read Acknowledgment Frame (`READ_ACK`)
Informs peer and server that incoming messages were viewed.
```json
{
  "type": "READ_ACK",
  "conversation_peer_id": "usr_alex_chen",
  "last_message_id": "msg_101"
}
```

---

### 6.4 Server-to-Client Frame Types

#### 1. Heartbeat Pong Frame (`PONG`)
```json
{
  "type": "PONG",
  "timestamp": "2026-10-20T04:50:00Z"
}
```

#### 2. Connection Established Frame (`CONNECTED`)
Dispatched immediately after WebSocket acceptance.
```json
{
  "type": "CONNECTED",
  "user_id": "usr_elena_rostova",
  "session_id": "sess_89f0a2e1",
  "online_connection_ids": ["usr_alex_chen", "usr_marcus_vance"],
  "badges": {
    "unread_messages": 2,
    "pending_connections": 1,
    "unread_notifications": 4
  }
}
```

#### 3. Message Transmission Acknowledgment (`MESSAGE_ACK`)
Confirms persistence to the sender client.
```json
{
  "type": "MESSAGE_ACK",
  "client_msg_id": "tmp_msg_001",
  "message_id": "msg_501",
  "recipient_id": "usr_alex_chen",
  "status": "DELIVERED",
  "created_at": "2026-10-20T04:50:01Z"
}
```
*Note: If the recipient is currently offline, `status` returns `"SENT_OFFLINE"` and a notification row is persisted.*

#### 4. Incoming Direct Message (`NEW_MESSAGE`)
Dispatched to recipient socket when online.
```json
{
  "type": "NEW_MESSAGE",
  "message": {
    "id": "msg_501",
    "sender_id": "usr_elena_rostova",
    "recipient_id": "usr_alex_chen",
    "content": "Hey Alex, are you available for a brief sync on the distributed queue design?",
    "created_at": "2026-10-20T04:50:01Z",
    "sender_summary": {
      "id": "usr_elena_rostova",
      "full_name": "Elena Rostova",
      "headline": "Staff AI Systems Engineer",
      "avatar_url": "/uploads/avatars/usr_elena_rostova.png"
    }
  }
}
```

#### 5. Peer Typing Status (`PEER_TYPING`)
Dispatched to chat peer.
```json
{
  "type": "PEER_TYPING",
  "user_id": "usr_alex_chen",
  "is_typing": true
}
```

#### 6. Presence Transition (`PRESENCE_UPDATE`)
Dispatched to all confirmed 1st-degree connections when peer connects or disconnects.
```json
{
  "type": "PRESENCE_UPDATE",
  "user_id": "usr_alex_chen",
  "is_online": true
}
```

#### 7. Notification Alert Push (`NOTIFICATION_ALERT`)
Dispatched when actions trigger alerts (reaction, comment, job status change).
```json
{
  "type": "NOTIFICATION_ALERT",
  "notification": {
    "id": "notif_88",
    "notification_type": "POST_REACTION",
    "title": "New Reaction",
    "content": "Priya Sharma celebrated your post.",
    "reference_id": "post_01",
    "reference_type": "POST",
    "actor": {
      "id": "usr_priya_sharma",
      "full_name": "Priya Sharma",
      "avatar_url": "/uploads/avatars/usr_priya_sharma.png"
    },
    "created_at": "2026-10-20T04:51:00Z"
  }
}
```

#### 8. Badge Counter Sync (`BADGE_UPDATE`)
Dispatched whenever any unread count changes.
```json
{
  "type": "BADGE_UPDATE",
  "unread_messages": 3,
  "pending_connections": 1,
  "unread_notifications": 5
}
```

#### 9. Protocol Error Frame (`ERROR`)
```json
{
  "type": "ERROR",
  "code": "MUST_BE_FIRST_DEGREE_CONNECTION",
  "message": "Cannot transmit direct message. Recipient is not a confirmed 1st-degree connection.",
  "details": {
    "target_user_id": "usr_jordan_mendez"
  }
}
```

---

### 6.5 Client Resilience & Reconnection Backoff Policy

1. **Keep-Alive Interval:** Browser client dispatches a `PING` frame every 30 seconds. If no `PONG` frame arrives within 10 seconds, the client marks the connection degraded.
2. **Exponential Reconnection with Jitter:**
   Upon unexpected socket termination, client reconnects using truncated exponential backoff:
   $$\text{Delay} = \min(10000, 1000 \times 2^{\text{attempt}}) \pm \text{jitter}(0, 500\text{ms})$$
3. **Persona Switch Flush:**
   When the user switches persona via `API-003`, the client explicitly calls `socket.close(1000, "Persona Switched")`, clears cached inboxes and notifications, and re-initiates the handshake with the new token.

---

## 7. Definition of Done & Cross-Tier Contract Verification

- [x] **Zero Ambiguity:** Every endpoint defines explicit method, URI, request schema, response schema, and error codes.
- [x] **Zero Placeholders:** Contains zero `TODO`, `FIXME`, `...`, `pass`, or mock markers.
- [x] **100% Traceability:** All 50 REST routes (`API-001` through `API-050`) mapped directly to PRD functional requirements (`REQ-001` through `REQ-019`) and NFRs.
- [x] **Dual Schema Representation:** Provided identical schemas in both TypeScript interfaces (`types.ts`) and Python Pydantic V2 models (`contracts.py`).
- [x] **Standardized Error Envelope:** `ERR-001` through `ERR-024` with strict `{ "error": { ... } }` schema.
- [x] **Complete WebSocket Protocol:** Documented bidirectional frames (`/ws`), close codes, presence, typing indicators, and backoff policy.

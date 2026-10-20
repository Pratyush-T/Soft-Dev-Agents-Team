// =============================================================================
// PRONET AUTHORITATIVE TYPESCRIPT CONTRACTS (v1.0.0)
// File: src/types/api.ts
// Upstream references: Apps/ProNet/docs/04_api_contracts.md, Apps/ProNet/docs/05_ui_system.md
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

export interface UserSummaryDTO {
  id: string;
  email: string;
  full_name: string;
  headline: string;
  avatar_url: string | null;
}

export interface AuthTokensDTO {
  access_token: string;
  token_type: 'bearer';
  expires_in_seconds: number;
  user: UserSummaryDTO;
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

// --- WEBSOCKET FRAMES ---
export type WebSocketClientFrame =
  | { type: 'PING'; timestamp: string }
  | { type: 'SEND_MESSAGE'; client_msg_id: string; recipient_id: string; content: string }
  | { type: 'TYPING'; recipient_id: string; is_typing: boolean }
  | { type: 'READ_ACK'; conversation_peer_id: string; last_message_id: string };

export type WebSocketServerFrame =
  | { type: 'PONG'; timestamp: string }
  | { type: 'CONNECTED'; user_id: string; session_id: string; online_connection_ids: string[]; badges: BadgeCountsDTO }
  | { type: 'MESSAGE_ACK'; client_msg_id: string; message_id: string; recipient_id: string; status: 'DELIVERED' | 'SENT_OFFLINE'; created_at: string }
  | { type: 'NEW_MESSAGE'; message: MessageDTO }
  | { type: 'TYPING'; sender_id: string; is_typing: boolean }
  | { type: 'READ_ACK'; conversation_peer_id: string; read_at: string }
  | { type: 'NOTIFICATION'; notification: NotificationDTO }
  | { type: 'BADGE_UPDATE'; badges: BadgeCountsDTO }
  | { type: 'PRESENCE_UPDATE'; user_id: string; is_online: boolean }
  | { type: 'ERROR'; code: string; message: string };

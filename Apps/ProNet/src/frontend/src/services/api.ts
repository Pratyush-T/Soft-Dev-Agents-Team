import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  AuthTokensDTO,
  BadgeCountsDTO,
  CommentDTO,
  ConnectionDTO,
  CreateCommentDTO,
  CreateJobDTO,
  CreatePostDTO,
  CursorPaginatedResponse,
  EasyApplyDTO,
  EducationCreateDTO,
  EducationDTO,
  EducationUpdateDTO,
  ExperienceCreateDTO,
  ExperienceDTO,
  ExperienceUpdateDTO,
  FeedMode,
  JobApplicationDTO,
  JobDTO,
  JobFilterParams,
  JobStatus,
  LoginRequestDTO,
  MessageDTO,
  ConversationSummaryDTO,
  NotificationDTO,
  PendingConnectionsDTO,
  PersonaDTO,
  PostDTO,
  PostReactionDTO,
  ProfileDetailDTO,
  ProfileUpdateDTO,
  RegisterRequestDTO,
  SendConnectionRequestDTO,
  SetReactionDTO,
  SkillDTO,
  UpdateApplicationStatusDTO,
  UploadResponseDTO,
  UserSummaryDTO,
} from '../types/api';

const BASE_URL = '/api/v1';

export class ApiError extends Error {
  code: string;
  statusCode: number;
  details?: Record<string, unknown>;

  constructor(code: string, message: string, statusCode: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to attach bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('pronet_jwt') || sessionStorage.getItem('pronet_jwt');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to format errors into standard ApiError
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: { code?: string; message?: string; details?: Record<string, unknown> } }>) => {
    if (error.response?.data?.error) {
      const err = error.response.data.error;
      return Promise.reject(
        new ApiError(
          err.code || 'ERR_UNKNOWN',
          err.message || 'An unexpected error occurred.',
          error.response.status,
          err.details
        )
      );
    }
    return Promise.reject(
      new ApiError(
        'ERR_NETWORK',
        error.message || 'Network connection failed.',
        error.response?.status || 500
      )
    );
  }
);

export const api = {
  // Auth & Personas
  auth: {
    register: async (payload: RegisterRequestDTO): Promise<AuthTokensDTO> => {
      const res = await apiClient.post<AuthTokensDTO>('/auth/register', payload);
      return res.data;
    },
    login: async (payload: LoginRequestDTO): Promise<AuthTokensDTO> => {
      const res = await apiClient.post<AuthTokensDTO>('/auth/login', payload);
      return res.data;
    },
    quickSwitch: async (userId: string): Promise<AuthTokensDTO> => {
      const res = await apiClient.post<AuthTokensDTO>('/auth/quick-switch', { user_id: userId });
      return res.data;
    },
    getPersonas: async (): Promise<PersonaDTO[]> => {
      const res = await apiClient.get<PersonaDTO[]>('/auth/personas');
      return res.data;
    },
    getMe: async (): Promise<UserSummaryDTO> => {
      const res = await apiClient.get<UserSummaryDTO>('/auth/me');
      return res.data;
    },
  },

  // Users & Profiles
  users: {
    getProfile: async (userId: string): Promise<ProfileDetailDTO> => {
      const res = await apiClient.get<ProfileDetailDTO>(`/users/${userId}`);
      return res.data;
    },
    updateProfile: async (payload: ProfileUpdateDTO): Promise<ProfileDetailDTO> => {
      const res = await apiClient.patch<ProfileDetailDTO>('/users/me/profile', payload);
      return res.data;
    },
    getMutuals: async (userId: string): Promise<UserSummaryDTO[]> => {
      const res = await apiClient.get<UserSummaryDTO[]>(`/users/${userId}/mutuals`);
      return res.data;
    },
    addExperience: async (payload: ExperienceCreateDTO): Promise<ExperienceDTO> => {
      const res = await apiClient.post<ExperienceDTO>('/users/me/experiences', payload);
      return res.data;
    },
    updateExperience: async (id: string, payload: ExperienceUpdateDTO): Promise<ExperienceDTO> => {
      const res = await apiClient.put<ExperienceDTO>(`/users/me/experiences/${id}`, payload);
      return res.data;
    },
    deleteExperience: async (id: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/users/me/experiences/${id}`);
      return res.data;
    },
    addEducation: async (payload: EducationCreateDTO): Promise<EducationDTO> => {
      const res = await apiClient.post<EducationDTO>('/users/me/educations', payload);
      return res.data;
    },
    updateEducation: async (id: string, payload: EducationUpdateDTO): Promise<EducationDTO> => {
      const res = await apiClient.put<EducationDTO>(`/users/me/educations/${id}`, payload);
      return res.data;
    },
    deleteEducation: async (id: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/users/me/educations/${id}`);
      return res.data;
    },
    getSkills: async (query?: string): Promise<SkillDTO[]> => {
      const res = await apiClient.get<SkillDTO[]>('/skills', { params: { q: query } });
      return res.data;
    },
    addSkill: async (skillName: string): Promise<SkillDTO> => {
      const res = await apiClient.post<SkillDTO>('/users/me/skills', { skill_name: skillName });
      return res.data;
    },
    removeSkill: async (skillId: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/users/me/skills/${skillId}`);
      return res.data;
    },
  },

  // Social Connections
  connections: {
    getConnections: async (): Promise<ConnectionDTO[]> => {
      const res = await apiClient.get<ConnectionDTO[]>('/connections');
      return res.data;
    },
    getPending: async (): Promise<PendingConnectionsDTO> => {
      const res = await apiClient.get<PendingConnectionsDTO>('/connections/pending');
      return res.data;
    },
    sendRequest: async (payload: SendConnectionRequestDTO): Promise<ConnectionDTO> => {
      const res = await apiClient.post<ConnectionDTO>('/connections/request', payload);
      return res.data;
    },
    acceptRequest: async (connectionId: string): Promise<ConnectionDTO> => {
      const res = await apiClient.post<ConnectionDTO>(`/connections/${connectionId}/accept`);
      return res.data;
    },
    ignoreRequest: async (connectionId: string): Promise<{ success: boolean }> => {
      const res = await apiClient.post<{ success: boolean }>(`/connections/${connectionId}/ignore`);
      return res.data;
    },
    withdrawRequest: async (connectionId: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/connections/${connectionId}/withdraw`);
      return res.data;
    },
    disconnect: async (userId: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/connections/${userId}`);
      return res.data;
    },
  },

  // Feed & Posts
  feed: {
    getFeed: async (mode: FeedMode = 'recent', cursor?: string, limit: number = 20): Promise<CursorPaginatedResponse<PostDTO>> => {
      const res = await apiClient.get<CursorPaginatedResponse<PostDTO>>('/feed', {
        params: { mode, cursor, limit },
      });
      return res.data;
    },
    createPost: async (payload: CreatePostDTO): Promise<PostDTO> => {
      const res = await apiClient.post<PostDTO>('/posts', payload);
      return res.data;
    },
    getPost: async (postId: string): Promise<PostDTO> => {
      const res = await apiClient.get<PostDTO>(`/posts/${postId}`);
      return res.data;
    },
    deletePost: async (postId: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/posts/${postId}`);
      return res.data;
    },
    setReaction: async (postId: string, payload: SetReactionDTO): Promise<PostReactionDTO> => {
      const res = await apiClient.post<PostReactionDTO>(`/posts/${postId}/reactions`, payload);
      return res.data;
    },
    removeReaction: async (postId: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/posts/${postId}/reactions`);
      return res.data;
    },
    getComments: async (postId: string): Promise<CommentDTO[]> => {
      const res = await apiClient.get<CommentDTO[]>(`/posts/${postId}/comments`);
      return res.data;
    },
    addComment: async (postId: string, payload: CreateCommentDTO): Promise<CommentDTO> => {
      const res = await apiClient.post<CommentDTO>(`/posts/${postId}/comments`, payload);
      return res.data;
    },
    deleteComment: async (commentId: string): Promise<{ success: boolean }> => {
      const res = await apiClient.delete<{ success: boolean }>(`/comments/${commentId}`);
      return res.data;
    },
  },

  // Jobs & ATS
  jobs: {
    getJobs: async (filters: JobFilterParams = {}): Promise<CursorPaginatedResponse<JobDTO>> => {
      const res = await apiClient.get<CursorPaginatedResponse<JobDTO>>('/jobs', {
        params: filters,
      });
      return res.data;
    },
    getJob: async (jobId: string): Promise<JobDTO> => {
      const res = await apiClient.get<JobDTO>(`/jobs/${jobId}`);
      return res.data;
    },
    createJob: async (payload: CreateJobDTO): Promise<JobDTO> => {
      const res = await apiClient.post<JobDTO>('/jobs', payload);
      return res.data;
    },
    updateJobStatus: async (jobId: string, status: JobStatus): Promise<JobDTO> => {
      const res = await apiClient.patch<JobDTO>(`/jobs/${jobId}/status`, { status });
      return res.data;
    },
    apply: async (jobId: string, payload: EasyApplyDTO): Promise<JobApplicationDTO> => {
      const res = await apiClient.post<JobApplicationDTO>(`/jobs/${jobId}/apply`, payload);
      return res.data;
    },
    getApplications: async (jobId: string): Promise<JobApplicationDTO[]> => {
      const res = await apiClient.get<JobApplicationDTO[]>(`/jobs/${jobId}/applications`);
      return res.data;
    },
    updateApplicationStatus: async (
      jobId: string,
      applicationId: string,
      payload: UpdateApplicationStatusDTO
    ): Promise<JobApplicationDTO> => {
      const res = await apiClient.patch<JobApplicationDTO>(
        `/jobs/${jobId}/applications/${applicationId}/status`,
        payload
      );
      return res.data;
    },
    getMyApplications: async (): Promise<JobApplicationDTO[]> => {
      const res = await apiClient.get<JobApplicationDTO[]>('/jobs/applications/me');
      return res.data;
    },
  },

  // Messaging & Real-Time
  messages: {
    getConversations: async (): Promise<ConversationSummaryDTO[]> => {
      const res = await apiClient.get<ConversationSummaryDTO[]>('/messages/conversations');
      return res.data;
    },
    getMessages: async (peerId: string, cursor?: string, limit: number = 50): Promise<CursorPaginatedResponse<MessageDTO>> => {
      const res = await apiClient.get<CursorPaginatedResponse<MessageDTO>>(`/messages/${peerId}`, {
        params: { cursor, limit },
      });
      return res.data;
    },
    markRead: async (peerId: string): Promise<{ marked_count: number }> => {
      const res = await apiClient.post<{ marked_count: number }>(`/messages/${peerId}/read`);
      return res.data;
    },
  },

  // Notifications
  notifications: {
    getNotifications: async (cursor?: string, limit: number = 20): Promise<CursorPaginatedResponse<NotificationDTO>> => {
      const res = await apiClient.get<CursorPaginatedResponse<NotificationDTO>>('/notifications', {
        params: { cursor, limit },
      });
      return res.data;
    },
    markRead: async (notificationIds?: string[]): Promise<{ success: boolean; marked_count: number }> => {
      const res = await apiClient.post<{ success: boolean; marked_count: number }>('/notifications/read', {
        notification_ids: notificationIds,
      });
      return res.data;
    },
    getBadges: async (): Promise<BadgeCountsDTO> => {
      const res = await apiClient.get<BadgeCountsDTO>('/notifications/badges');
      return res.data;
    },
  },

  // File Uploads
  uploads: {
    uploadAvatar: async (file: File): Promise<UploadResponseDTO> => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post<UploadResponseDTO>('/uploads/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    uploadPostMedia: async (file: File): Promise<UploadResponseDTO> => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post<UploadResponseDTO>('/uploads/post-media', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    uploadResume: async (file: File): Promise<UploadResponseDTO> => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post<UploadResponseDTO>('/uploads/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
  },
};

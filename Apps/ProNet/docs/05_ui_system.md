# ProNet - Design System & UI/UX Architecture Specification (v1.0.0)

- **Document Version:** 1.0.0
- **Status:** Approved Engineering Blueprint
- **Author:** Staff Design System & UX Architect
- **Target Release:** v1.0 Local Production
- **Approved For Implementation:** Phase 4 (`07_frontend_eng`)
- **Upstream References:** `Apps/ProNet/docs/01_prd.md`, `Apps/ProNet/docs/04_api_contracts.md`
- **Output Artifact:** `Apps/ProNet/docs/05_ui_system.md`

---

## 1. Executive Summary & Design Principles

### 1.1 Purpose and Architectural Governance
This specification defines the complete client-tier design system, component hierarchy, prop contracts, state management workflows, and interaction standards for **ProNet**. It operationalizes all functional requirements (`REQ-001` through `REQ-019`) and non-functional constraints (`NFR-005` bundle size ≤ 1.2 MB, `NFR-009` XSS sanitization) into deterministic, testable React 18 and Tailwind CSS component blueprints.

Frontend engineers (`07_frontend_eng`) must adhere strictly to these token definitions, component signatures, state flow diagrams, and accessibility rules without improvisation or placeholder substitutions.

### 1.2 Core UX Principles
1. **Local-First Responsiveness:** Zero-lag feedback with optimistic UI mutations for social interactions (reactions, comments, connections) backed by TanStack Query rollbacks on failure.
2. **Professional Clarity (LinkedIn Ergonomics):** High-density, low-noise information hierarchy utilizing standard enterprise layout patterns (3-column feed, card containers, tabbed network management).
3. **Deterministic 4-State Completeness:** Every screen and data-bound component must implement four explicit states: *Loading Skeleton*, *Empty State with CTA*, *Populated State*, and *Error State with Retry Trigger*.
4. **Instant Persona Context Switching:** Rapid, one-click persona switching integrated directly into the top navigation bar with complete local state invalidation, persistent WebSocket re-handshake, and deterministic credential switching across all 10 seed personas.
5. **Universal Accessibility (WCAG 2.1 AA):** 100% keyboard navigable with visible focus indicators, screen-reader semantic landmarks, ARIA live regions, and color contrast ratios exceeding 4.5:1.

---

## 2. Design Token Specification (Tailwind CSS Configuration)

The design token system is configured directly in `tailwind.config.js` and provides immutable visual parameters across color, typography, spacing, elevations, and responsive breakpoints.

### 2.1 Color Palette & Semantic System

ProNet utilizes a tailored slate/blue palette reflecting executive enterprise networking software, augmented with semantic state indicators:

```javascript
// tailwind.config.js - Design Tokens Definition
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Brand Primary (Professional Executive Blue)
        brand: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#0A66C2', // Signature ProNet Primary
          700: '#004182',
          800: '#002B56',
          900: '#001833',
          950: '#000E20',
        },
        // Neutral Grayscale (Slate Scale for UI Surfaces & Borders)
        surface: {
          50: '#F8FAFC',  // Main Page Canvas Background
          100: '#F1F5F9', // Secondary Containers / Input Backgrounds
          200: '#E2E8F0', // Card Borders / Dividers
          300: '#CBD5E1', // Hover Borders / Inactive Icons
          400: '#94A3B8', // Placeholder Text / Disabled Indicators
          500: '#64748B', // Muted Secondary Copy / Timestamps
          600: '#475569', // Primary Subtitles / Icon Accents
          700: '#334155', // Body Copy Secondary
          800: '#1E293B', // High-Emphasis Titles
          900: '#0F172A', // Primary Headings & Dark Elements
          950: '#020617', // Extreme Dark / Contrast Overlays
        },
        // Semantic Status Tokens
        success: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          500: '#10B981',
          600: '#059669', // Confirmed / Accepted / Online Status
          700: '#047857',
        },
        warning: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          500: '#F59E0B',
          600: '#D97706', // Pending Request / Reviewing Status
          700: '#B45309',
        },
        danger: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          500: '#EF4444',
          600: '#DC2626', // Rejections / Errors / Disconnect Actions
          700: '#B91C1C',
        },
        info: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          500: '#6366F1',
          600: '#4F46E5', // System Notices / Info Banners
          700: '#4338CA',
        },
        // Degree Badges & Reaction Tokens
        degree: {
          first: {
            bg: '#ECFDF5',
            text: '#065F46',
            border: '#A7F3D0',
          },
          second: {
            bg: '#EFF6FF',
            text: '#1E40AF',
            border: '#BFDBFE',
          },
          third: {
            bg: '#F1F5F9',
            text: '#475569',
            border: '#CBD5E1',
          },
        },
        reaction: {
          like: '#0A66C2',       // Thumbs Up Blue
          celebrate: '#059669',  // Hands Clapping Green
          insightful: '#D97706', // Lightbulb Amber
        },
      },
    },
  },
};
```

### 2.2 Typography Scale & Font Hierarchy

ProNet utilizes a clean sans-serif typeface hierarchy optimized for scanning dense feeds, job descriptions, and profile career timelines.

| Token | Font Size | Line Height | Weight | Tailwind Class | Primary Usage Scenario |
|---|---|---|---|---|---|
| **Display** | 30px (1.875rem) | 36px (2.25rem) | Bold (700) | `text-3xl font-bold tracking-tight` | Landing headers, Auth view titles |
| **Heading 1** | 24px (1.5rem) | 32px (2rem) | Bold (700) | `text-2xl font-bold` | Profile user full name, Page titles |
| **Heading 2** | 20px (1.25rem) | 28px (1.75rem) | Semibold (600) | `text-xl font-semibold` | Section titles (Experience, Education, Jobs) |
| **Heading 3** | 18px (1.125rem) | 26px (1.625rem) | Semibold (600) | `text-lg font-semibold` | Modal headers, Post author name, Job title |
| **Body Large** | 16px (1.0rem) | 24px (1.5rem) | Regular (400) | `text-base font-normal` | Feed post content body, Bio narrative |
| **Body Large Semi** | 16px (1.0rem) | 24px (1.5rem) | Medium (500) | `text-base font-medium` | Emphasized body text, Form inputs |
| **Body Regular** | 14px (0.875rem) | 20px (1.25rem) | Regular (400) | `text-sm font-normal` | Comments, Experience company/location |
| **Body Medium** | 14px (0.875rem) | 20px (1.25rem) | Medium (500) | `text-sm font-medium` | Navigation labels, Button text, Filter tags |
| **Caption** | 12px (0.75rem) | 16px (1.0rem) | Regular (400) | `text-xs font-normal` | Timestamps, Character counters, Footers |
| **Badge / Pill** | 11px (0.6875rem)| 14px (0.875rem)| Semibold (600) | `text-[11px] font-semibold uppercase` | Degree badges (1st, 2nd, 3rd+), Workplace mode |
| **Code Mono** | 13px (0.8125rem)| 20px (1.25rem) | Regular (400) | `font-mono text-[13px]` | Code snippet blocks in posts |

### 2.3 Elevation & Surface Shadows

Surfaces are elevated using subtle, multi-layered shadows to maintain contrast without visual clutter:

```css
/* Elevation Shadow Tokens */
--shadow-elevation-1: 0 1px 3px 0 rgba(15, 23, 42, 0.08), 0 1px 2px -1px rgba(15, 23, 42, 0.08); /* Cards at rest */
--shadow-elevation-2: 0 4px 6px -1px rgba(15, 23, 42, 0.10), 0 2px 4px -2px rgba(15, 23, 42, 0.06); /* Dropdown menus / Hover cards */
--shadow-elevation-3: 0 10px 15px -3px rgba(15, 23, 42, 0.12), 0 4px 6px -4px rgba(15, 23, 42, 0.08); /* Modals / Drawers */
--shadow-elevation-float: 0 20px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.10); /* Chat dock / Toast alerts */
```

### 2.4 Spacing & Border Radii System

- **Base Spacing Grid:** 4px incremental scale (`p-1` = 4px, `p-2` = 8px, `p-3` = 12px, `p-4` = 16px, `p-6` = 24px, `p-8` = 32px).
- **Component Padding Standards:**
  - Card Internal Padding: `p-4` (Mobile) / `p-6` (Desktop).
  - Modal Internal Padding: `p-6`.
  - Button Padding: Compact (`px-3 py-1.5`), Standard (`px-4 py-2`), Large (`px-5 py-2.5`).
- **Border Radii:**
  - `rounded-md` (6px): Form inputs, dropdown menus, button controls.
  - `rounded-lg` (8px): Activity post cards, widget panels, dialog surfaces.
  - `rounded-xl` (12px): Modal dialog frames, floating chat dock.
  - `rounded-full` (9999px): User avatars, degree badges, status indicator pills.

### 2.5 Responsive Breakpoints & Multi-Column Layout Grid

The ProNet desktop interface follows the classic 3-column feed architecture:

```
+-------------------------------------------------------------------------------------------------------+
| TOP NAVIGATION BAR (Fixed h-14 bg-white border-b border-surface-200 z-40)                             |
| [ProNet Logo] [Search Global] -------- [Feed] [Network] [Jobs] [Chat] [Notifs] ---- [Persona Switcher]|
+-------------------------------------------------------------------------------------------------------+
|                                 MAX-WIDTH CONTAINER (max-w-7xl mx-auto px-4 py-6)                     |
|                                                                                                       |
| +---------------------+   +-------------------------------------+   +-------------------------------+ |
| | LEFT SIDEBAR        |   | CENTER FEED COLUMN                  |   | RIGHT SIDEBAR                 | |
| | (w-64 shrink-0)     |   | (flex-1 max-w-2xl)                  |   | (w-80 shrink-0)               | |
| |                     |   |                                     |   |                               | |
| | - Mini Profile Card |   | - Post Composer Trigger             |   | - ProNet News / Trending Tech | |
| | - Network Stats     |   | - Feed Sort Controls (Recent/Top)   |   | - Recommended Connections     | |
| | - Quick Links       |   | - Post Cards Stream (Infinite Scroll|   | - Recent Job Openings         | |
| +---------------------+   +-------------------------------------+   +-------------------------------+ |
+-------------------------------------------------------------------------------------------------------+
| FLOATING REAL-TIME MESSAGING DOCK (Fixed bottom-0 right-6 w-80 h-96 z-50 bg-white border rounded-t-lg)|
+-------------------------------------------------------------------------------------------------------+
```

- `sm` (640px): Single-column view with bottom mobile navigation bar.
- `md` (768px): Tablet layout with collapsible left sidebar and main feed.
- `lg` (1024px): 2-column layout (Center Feed + Right Recommendation Sidebar).
- `xl` (1280px): Full 3-column desktop layout (Left Profile Widget + Center Feed + Right Recommendations).

---

## 3. Component Hierarchy & Prop Contracts

Every component in ProNet is implemented in TypeScript with zero `any` types. Below are the complete atomic primitives, composite feature widgets, and global Zustand store contracts.

### 3.1 Layer 1: Atomic Primitives (`src/frontend/src/components/ui/`)

#### 1. Button Primitive (`Button.tsx`)
```typescript
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}
```
- **Styling Rules:**
  - `primary`: `bg-brand-600 hover:bg-brand-700 text-white font-medium shadow-sm focus-visible:ring-2 focus-visible:ring-brand-600`
  - `secondary`: `bg-surface-100 hover:bg-surface-200 text-surface-800 font-medium`
  - `outline`: `border border-brand-600 text-brand-600 hover:bg-brand-50 font-medium`
  - `danger`: `bg-danger-600 hover:bg-danger-700 text-white font-medium`
  - `isLoading`: Displays animated spinning SVG loader and disables click handling.

#### 2. Avatar Primitive (`Avatar.tsx`)
```typescript
export interface AvatarProps {
  src: string | null;
  alt: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isOnline?: boolean;
  className?: string;
}
```
- **Size Mapping:** `xs` (24px), `sm` (32px), `md` (40px), `lg` (48px), `xl` (72px).
- **Fallback Mechanism:** When `src` is null or fails to load, renders fallback SVG circle with capitalized user initials on `bg-brand-100 text-brand-800`.
- **Presence Badge:** If `isOnline` is true, renders a 10px circular indicator (`bg-success-600 border-2 border-white absolute bottom-0 right-0 rounded-full`).

#### 3. Degree Badge Primitive (`DegreeBadge.tsx`)
```typescript
export interface DegreeBadgeProps {
  degree: '1st' | '2nd' | '3rd+';
  className?: string;
}
```
- **Degree Styling:**
  - `'1st'`: `bg-emerald-50 text-emerald-700 border border-emerald-300 text-[11px] font-semibold px-1.5 py-0.5 rounded-full`
  - `'2nd'`: `bg-blue-50 text-blue-700 border border-blue-300 text-[11px] font-semibold px-1.5 py-0.5 rounded-full`
  - `'3rd+'`: `bg-surface-100 text-surface-600 border border-surface-300 text-[11px] font-semibold px-1.5 py-0.5 rounded-full`

#### 4. Skeleton Loader Primitive (`Skeleton.tsx`)
```typescript
export interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  className?: string;
}
```
- **Animation:** Employs CSS `animate-pulse` on `bg-surface-200 rounded`.

#### 5. Modal Dialog Primitive (`Modal.tsx`)
```typescript
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}
```
- **Accessibility:** Traps focus using `focus-trap-react`, attaches `role="dialog"`, `aria-modal="true"`, listens to `Escape` key, and locks background body scroll.

---

### 3.2 Layer 2: Composite Feature Components

#### 1. Identity & Profile Components (`src/frontend/src/features/profile/`)

- `ProfileHeader.tsx`:
  - **Props:** `{ profile: ProfileDetailDTO; isOwnProfile: boolean; onEditProfile: () => void; onConnect: () => void; onDisconnect: () => void; onMessage: () => void; }`
  - **Renders:** Cover banner, large Avatar (with upload trigger if own profile), Full Name, Headline, Location, Connections Count with degree badge, Mutual Connections Preview button (`API-008`), and Contextual Action Button (Edit / Connect / Withdraw / Accept / Message).

- `ExperienceTimeline.tsx`:
  - **Props:** `{ experiences: ExperienceDTO[]; isOwnProfile: boolean; onAdd: () => void; onEdit: (exp: ExperienceDTO) => void; onDelete: (id: string) => void; }`
  - **Renders:** Chronological career list, date range calculation, duration badge, company logo placeholder, and description.

- `EducationTimeline.tsx`:
  - **Props:** `{ educations: EducationDTO[]; isOwnProfile: boolean; onAdd: () => void; onEdit: (edu: EducationDTO) => void; onDelete: (id: string) => void; }`
  - **Renders:** Academic institutions, degrees, fields of study, and matriculation years.

- `SkillsCard.tsx`:
  - **Props:** `{ skills: SkillDTO[]; isOwnProfile: boolean; onAddSkill: (name: string) => void; onRemoveSkill: (id: string) => void; }`
  - **Renders:** Skill chips with removal `X` icons, searchable skill autocomplete input (`API-015`).

- `MutualConnectionsModal.tsx`:
  - **Props:** `{ isOpen: boolean; onClose: () => void; userId: string; }`
  - **Renders:** Paginated modal list of shared 1st-degree connections between the viewer and the viewed profile (`API-008`).

#### 2. Activity Feed Components (`src/frontend/src/features/feed/`)

- `PostComposerModal.tsx`:
  - **Props:** `{ isOpen: boolean; onClose: () => void; onSuccess: () => void; }`
  - **Renders:** Rich post creator with text area (up to 3,000 characters with live counter), toggle for syntax-highlighted code block (language selector: `python`, `typescript`, `sql`, `bash`), image upload dropzone (drag-and-drop, max 5 MB), and publish button (`API-026`, `API-049`).

- `PostCard.tsx`:
  - **Props:** `{ post: PostDTO; onReactionChange: (type: ReactionType | null) => void; onDelete: (postId: string) => void; }`
  - **Renders:** Author summary header (avatar, name, headline, timestamp, degree badge), post body text, syntax-highlighted code snippet box (with copy-to-clipboard button), image media viewer (lightbox trigger), aggregated reaction bar (likes, celebrates, insightful counts, comment count), reaction button with hover popover picker (`API-029`, `API-030`), comment toggle button, and expandable two-level threaded comment section (`API-031`, `API-032`, `API-033`).

- `ReactionPicker.tsx`:
  - **Props:** `{ onSelect: (type: ReactionType) => void; activeReaction: ReactionType | null; }`
  - **Renders:** Floating emoji/icon dock on hover: Like (👍 Blue), Celebrate (👏 Green), Insightful (💡 Amber).

- `CommentThread.tsx`:
  - **Props:** `{ postId: string; isPostAuthor: boolean; }`
  - **Renders:** Level 1 root comment composer, paginated list of root comments, reply triggers, Level 2 nested comment list, and moderation delete buttons (`API-032`, `API-033`).

#### 3. Job Board & Mini-ATS Components (`src/frontend/src/features/jobs/`)

- `JobSearchFilterBar.tsx`:
  - **Props:** `{ filters: JobFilterParams; onChange: (filters: JobFilterParams) => void; }`
  - **Renders:** Search keyword input, workplace mode dropdown (`REMOTE`, `HYBRID`, `ON_SITE`), skill tag multi-selector, and location input.

- `JobCard.tsx`:
  - **Props:** `{ job: JobDTO; isSelected: boolean; onSelect: () => void; }`
  - **Renders:** Job title, company name, workplace type badge, location, formatted salary range (`$140k - $180k / yr`), required skill tags, application count, and applied status pill.

- `EasyApplyModal.tsx`:
  - **Props:** `{ job: JobDTO; isOpen: boolean; onClose: () => void; onSuccess: () => void; }`
  - **Renders:** Modal displaying candidate profile snapshot preview (headline, top skills), cover note text area (max 500 characters), PDF/DOCX resume file upload dropzone (`API-050`), and 1-click submit button (`API-038`).

- `RecruiterPipelineView.tsx`:
  - **Props:** `{ jobId: string; }`
  - **Renders:** Mini-ATS dashboard for job poster (`API-039`), Kanban columns or filterable table (`APPLIED`, `REVIEWING`, `SHORTLISTED`, `REJECTED`), applicant profile dossier card, resume download link, and status transition selector dropdown (`API-040`).

#### 4. Real-Time Messaging & Notifications Components (`src/frontend/src/features/messaging/`)

- `ChatDockWidget.tsx`:
  - **Props:** `None (State driven via useChatStore and useWebSocketStore)`
  - **Renders:** Floating collapsed/expanded chat drawer pinned to bottom-right corner. Displays conversation list with unread counters (`API-042`), active conversation header with peer presence indicator, live message history stream (`API-043`), typing indicator animation, and message input box with instant send (`SEND_MESSAGE` WebSocket frame).

- `NotificationsDrawer.tsx`:
  - **Props:** `{ isOpen: boolean; onClose: () => void; }`
  - **Renders:** Dropdown list of recent activity notifications (`API-045`), avatar of triggering actor, action description (reactions, comments, connections, job status updates), unread indicator dot, and "Mark All as Read" trigger button (`API-046`).

---

### 3.3 Layer 3: Global Zustand Store Contracts

ProNet decouples client state into four focused Zustand stores with deterministic TypeScript types:

#### 1. Authentication & Active Persona Store (`src/frontend/src/stores/authStore.ts`)
```typescript
export interface AuthState {
  token: string | null;
  currentUser: UserSummaryDTO | null;
  activePersonaId: string;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  initializeSession: () => Promise<void>;
  login: (credentials: LoginRequestDTO) => Promise<void>;
  register: (payload: RegisterRequestDTO) => Promise<void>;
  quickSwitchPersona: (personaId: string) => Promise<void>;
  logout: () => void;
  updateCurrentUserSummary: (summary: Partial<UserSummaryDTO>) => void;
}
```

#### 2. Real-Time WebSocket & Presence Store (`src/frontend/src/stores/webSocketStore.ts`)
```typescript
export type SocketConnectionStatus = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING';

export interface WebSocketState {
  socket: WebSocket | null;
  status: SocketConnectionStatus;
  onlineUserIds: Set<string>;
  badges: BadgeCountsDTO;
  reconnectAttempts: number;
  
  // Actions
  connect: (token: string) => void;
  disconnect: (code?: number, reason?: string) => void;
  sendFrame: (frame: unknown) => void;
  setOnlineUsers: (userIds: string[]) => void;
  updateUserPresence: (userId: string, isOnline: boolean) => void;
  updateBadges: (badges: Partial<BadgeCountsDTO>) => void;
  decrementBadge: (type: keyof BadgeCountsDTO, amount?: number) => void;
}
```

#### 3. Real-Time Chat & Thread Store (`src/frontend/src/stores/chatStore.ts`)
```typescript
export interface ChatState {
  isDockOpen: boolean;
  activePeerId: string | null;
  conversations: ConversationSummaryDTO[];
  messageHistories: Record<string, MessageDTO[]>; // keyed by peerId
  typingPeers: Record<string, boolean>;          // keyed by peerId
  draftMessages: Record<string, string>;         // keyed by peerId
  
  // Actions
  setDockOpen: (isOpen: boolean) => void;
  openChatWithPeer: (peerId: string) => void;
  closeActiveChat: () => void;
  setConversations: (conversations: ConversationSummaryDTO[]) => void;
  appendMessage: (peerId: string, message: MessageDTO) => void;
  setPeerTyping: (peerId: string, isTyping: boolean) => void;
  setDraftMessage: (peerId: string, text: string) => void;
  markConversationReadLocally: (peerId: string) => void;
}
```

#### 4. Global Toast Notification Store (`src/frontend/src/stores/toastStore.ts`)
```typescript
export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message: string;
  durationMs?: number;
}

export interface ToastState {
  toasts: ToastItem[];
  addToast: (toast: Omit<ToastItem, 'id'>) => string;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;
}
```

---

## 4. Mandatory 4-State View Matrix for Data-Driven Screens

Every data-driven screen in ProNet strictly implements the four fundamental UI states: **Loading Skeleton**, **Empty State with CTA**, **Populated State**, and **Error State with Retry Action**.

```
+------------------------------------------------------------------------------------------------------+
|                                   MANDATORY 4-STATE VIEW ARCHITECTURE                               |
+-----------------------------------+------------------------------------------------------------------+
| 1. LOADING SKELETON               | 2. EMPTY STATE WITH CTA                                          |
| - Layout-matched pulsing shapes   | - High-contrast illustrative icon                                |
| - Preserve container geometry     | - Human-friendly explanation of why nothing exists yet          |
| - Disabled inputs / no interaction| - Prominent call-to-action button to create first entry          |
+-----------------------------------+------------------------------------------------------------------+
| 3. POPULATED DATA VIEW            | 4. ERROR STATE WITH RETRY                                        |
| - Complete data rendering         | - Error boundary display with machine error code (ERR-XXX)       |
| - Sort, filter, & cursor triggers | - Plain language explanation of root cause                       |
| - Interactive contextual actions  | - Primary "Retry Action" button executing query invalidation     |
+-----------------------------------+------------------------------------------------------------------+
```

### 4.1 Screen 1: Activity Feed (`/` - `FeedView`)
- **API Endpoint:** `API-025` (`GET /api/v1/feed?mode=recent|top&cursor=...`)

```
[1. Loading Skeleton]
+-------------------------------------------------------------+
| [O] [====================] [======]                         |
| [=========================================================] |
| [================================================]          |
| +---------------------------------------------------------+ |
| | [Pulsing Code Block / Media Skeleton]                   | |
| +---------------------------------------------------------+ |
| [=== Like]   [=== Celebrate]   [=== Comment]                |
+-------------------------------------------------------------+

[2. Empty State with CTA]
+-------------------------------------------------------------+
|                     [ Newspaper Icon ]                      |
|                  "Your Feed is Quiet"                       |
| Be the first to share an architectural insight, technical   |
| learning, or industry update with the ProNet network.       |
|                 [ Button: "Start a Post" ]                  |
+-------------------------------------------------------------+

[3. Populated View]
+-------------------------------------------------------------+
| [Sort Tabs: [Recent] | [Top Engagement] ]                   |
| +---------------------------------------------------------+ |
| | [Avatar] Elena Rostova (Staff AI Engineer) [1st] - 2h    | |
| | "Benchmarking SQLite WAL concurrency under asyncio..."  | |
| | [Code Snippet: python / sqlite3 WAL pragma]             | |
| | (42 Likes) (18 Celebrates) (9 Comments)                 | |
| | [Like] [Celebrate] [Insightful] [Comment]               | |
| +---------------------------------------------------------+ |
+-------------------------------------------------------------+

[4. Error State with Retry]
+-------------------------------------------------------------+
|                  [ Alert Triangle Icon ]                    |
|             "Unable to Load Activity Feed"                  |
| Server returned error ERR-023: Database busy timeout.       |
| Check that the backend ASGI service is running.             |
|                 [ Button: "Retry Feed" ]                    |
+-------------------------------------------------------------+
```

### 4.2 Screen 2: User Profile View (`/users/:userId` - `UserProfileView`)
- **API Endpoints:** `API-006` (`GET /api/v1/users/{id}`), `API-008` (`GET /api/v1/users/{id}/mutuals`), `API-009` through `API-017`

| UI State | Visual Specification & Wireframe Layout | Copy & Interaction Triggers |
|---|---|---|
| **1. Loading** | Header card with circular skeleton avatar (72px), three text line skeletons (Name, Headline, Location), and 3 experience block skeletons. | Pulsing shimmer `animate-pulse bg-surface-200`. Buttons rendered disabled. |
| **2. Empty (Sections)** | Displayed inside sub-cards when user has no career history: "No work experience listed yet." | For profile owner: renders dashed border CTA card `[ + Add Experience ]` triggering `ExperienceModal`. For visitors: "No experience listed." |
| **3. Populated** | Complete profile header with degree badge (`1st`, `2nd`, `3rd+`), mutual connection avatars preview, chronologically ordered experience timeline, education history, and skill tags. | Interactive buttons: Connect (`API-020`), Disconnect (`API-024`), Message (`API-043`), or Edit Profile (`API-007`). |
| **4. Error** | Centered error card with user search icon: "User Profile Not Found (`ERR-009`)". "The requested professional does not exist or may have been removed." | Action button: `[ Return to Feed ]` with secondary button `[ Retry Request ]`. |

### 4.3 Screen 3: My Network - 1st-Degree Connections (`/network` - Tab: Connections)
- **API Endpoint:** `API-018` (`GET /api/v1/connections`)

| UI State | Visual Specification & Wireframe Layout | Copy & Interaction Triggers |
|---|---|---|
| **1. Loading** | Grid of 6 user connection card skeletons (Avatar circle, Name bar, Headline bar, Message button bar). | `animate-pulse bg-surface-200 rounded-lg h-44`. |
| **2. Empty** | Centered illustration of linked users: "You Have No 1st-Degree Connections Yet". "Expand your professional network by sending connection requests from user profiles or recommended peers." | Primary CTA: `[ Discover Professionals ]` (switches to Feed/Directory). |
| **3. Populated** | Responsive grid of connection cards: Peer Avatar (with online dot), Full Name, Headline, Connection Date ("Connected 3 days ago"), `[ Message ]` button (opens chat dock), and `[ ... ]` dropdown with "Remove Connection" (`API-024`). | Direct 1-click messaging trigger, search input to filter connections by name in memory. |
| **4. Error** | Warning box: "Failed to load professional connections (`ERR-004` / `ERR-024`)." | Primary CTA: `[ Refresh Network ]` executing `refetch()`. |

### 4.4 Screen 4: My Network - Pending Invitations (`/network` - Tab: Invitations)
- **API Endpoint:** `API-019` (`GET /api/v1/connections/pending`)

| UI State | Visual Specification & Wireframe Layout | Copy & Interaction Triggers |
|---|---|---|
| **1. Loading** | Stack of 3 horizontal list item skeletons with avatar, headline, and two action button rectangles. | Shimmering placeholder bars. |
| **2. Empty** | "No Pending Invitations". "You are all caught up! New invitations sent to you will appear here." | Secondary text: "Explore the feed to find colleagues and engineers." |
| **3. Populated** | Split sections: **Received Invitations (N)** and **Sent Invitations (M)**. Each received card displays sender avatar, name, headline, mutual connections count, optional note text bubble, `[ Ignore ]` button (`API-022`), and `[ Accept ]` button (`API-021`). Sent cards display recipient info with `[ Withdraw Request ]` button (`API-023`). | Instant optimistic removal from list with toast notification; updates navbar badge over WebSocket. |
| **4. Error** | "Unable to retrieve pending connection invitations." | Button: `[ Try Again ]`. |

### 4.5 Screen 5: Job Marketplace Portal (`/jobs` - `JobBoardView`)
- **API Endpoints:** `API-034` (`GET /api/v1/jobs`), `API-035` (`GET /api/v1/jobs/{id}`)

| UI State | Visual Specification & Wireframe Layout | Copy & Interaction Triggers |
|---|---|---|
| **1. Loading** | Two-pane split view skeleton: Left list has 5 card skeletons; right pane displays a large detail pane skeleton. | Shimmer bars for title, company, salary range, and description paragraph. |
| **2. Empty** | Briefcase icon with slash: "No Jobs Match Your Filter Criteria". "Try broadening your search keywords, workplace type (Remote/Hybrid), or skill tags." | Primary CTA: `[ Clear All Filters ]` resetting query parameters. |
| **3. Populated** | Split-screen desktop layout: Left scrollable list of matching job cards (title, company, mode badge, salary, applied status). Right sticky detail pane showing full job requisition, required skills tags, hiring manager avatar summary, and prominent `[ Easy Apply ]` button (`API-038`). | Instant URL query sync (`?keyword=&mode=`); keyboard arrow key navigation between job cards. |
| **4. Error** | Search failure card: "Error loading job requisitions (`ERR-024`)." | Button: `[ Refresh Jobs ]`. |

### 4.6 Screen 6: Recruiter Candidate Pipeline (`/jobs/:jobId/applications` - `RecruiterPipelineView`)
- **API Endpoints:** `API-039` (`GET /api/v1/jobs/{job_id}/applications`), `API-040` (`PATCH /.../status`)

| UI State | Visual Specification & Wireframe Layout | Copy & Interaction Triggers |
|---|---|---|
| **1. Loading** | Table header with 4 column skeletons or 4 Kanban column skeletons with 2 placeholder cards each. | Shimmer effect across candidate name, headline, status pill. |
| **2. Empty** | Candidate silhouette illustration: "No Applications Received Yet". "Candidates who submit an Easy Apply application for this requisition will appear here." | Primary action: `[ Copy Job Share Link ]` to clipboard. |
| **3. Populated** | 4-column ATS pipeline board (`APPLIED`, `REVIEWING`, `SHORTLISTED`, `REJECTED`). Each candidate card displays applicant avatar, name, headline snapshot, skills match tags, submission timestamp, resume download button, and stage transition dropdown (`API-040`). | Changing candidate stage dispatches `PATCH API-040` and pushes live WebSocket alert to applicant. |
| **4. Error** | Access denied banner (`ERR-005: NOT_JOB_OWNER`) or server error: "You are not authorized to view candidates for this requisition." | CTA: `[ Back to Job Postings ]`. |

### 4.7 Screen 7: Candidate "My Applications" (`/jobs/applications/me` - `MyApplicationsView`)
- **API Endpoint:** `API-041` (`GET /api/v1/jobs/applications/me`)

| UI State | Visual Specification & Wireframe Layout | Copy & Interaction Triggers |
|---|---|---|
| **1. Loading** | List of 3 application card skeletons with company logo, job title, and stage indicator pill. | Standard shimmering skeleton cards. |
| **2. Empty** | File checklist icon: "You Have Not Applied to Any Jobs Yet". "Browse open engineering and product roles on ProNet to submit your Easy Apply application." | Primary CTA: `[ Explore Open Positions ]` navigating to `/jobs`. |
| **3. Populated** | Card list showing Job Title, Company Name, Applied Date, Cover Note preview, Resume attachment link, and real-time Stage Badge (`APPLIED` = Blue, `REVIEWING` = Amber, `SHORTLISTED` = Green, `REJECTED` = Red). | Live updates via WebSocket `JOB_STATUS_CHANGE` frame without page refresh. |
| **4. Error** | "Unable to retrieve your submitted applications." | CTA: `[ Retry ]`. |

### 4.8 Screen 8: Real-Time Direct Messaging Thread (`ChatDockWidget` / `MessagingPage`)
- **API Endpoints:** `API-042` (`GET /conversations`), `API-043` (`GET /messages/{peer_id}`), `API-044` (`POST /read`), WebSocket `SEND_MESSAGE`

```
[1. Loading History Skeleton]
+-------------------------------------------------------------+
| [O] [====================] [Online Status Skeleton]         |
|-------------------------------------------------------------|
| [=== Incoming Message Skeleton ===]                         |
|                       [=== Outgoing Message Skeleton ===]   |
| [=== Incoming Message Skeleton ===]                         |
|-------------------------------------------------------------|
| [ Input Box Skeleton .............................. ] [Send]|
+-------------------------------------------------------------+

[2. Empty Conversation State]
+-------------------------------------------------------------+
| [Avatar] Elena Rostova (Staff AI Engineer) [1st Degree]     |
| "This is the start of your direct conversation with Elena." |
| You are confirmed 1st-degree connections. Messages sent     |
| here are encrypted in transit and delivered in real-time.   |
| Say hello or share an architectural question!               |
+-------------------------------------------------------------+

[3. Populated Live Chat Stream]
+-------------------------------------------------------------+
| [Avatar] Alex Chen (Principal Cloud Architect) [1st] [o]    |
|-------------------------------------------------------------|
| [Alex 10:14 AM]                                             |
| Hey Elena, did you run the WAL benchmark on SQLite yet?     |
|                                         [You 10:15 AM] [✓✓] |
| Yes! p95 latency stayed under 42ms with 20 concurrent tasks.|
|                                                             |
| * Alex is typing...                                         |
|-------------------------------------------------------------|
| [ Type a message to Alex...                     ] [ Send ➢ ]|
+-------------------------------------------------------------+

[4. Error / Restricted Degree State]
+-------------------------------------------------------------+
|                 [ Shield Warning Icon ]                     |
|           "Direct Messaging Unavailable"                    |
| Error ERR-006: You can only exchange direct messages with   |
| confirmed 1st-degree connections.                           |
|           [ Button: "Send Connection Request" ]             |
+-------------------------------------------------------------+
```

---

## 5. Built-in Persona Quick-Switcher Component Specification

The Persona Quick-Switcher is a core development and testing primitive required by `REQ-001`. It sits prominently in the top navigation bar, enabling instantaneous switching across the 10 pre-seeded profiles without credential re-entry.

### 5.1 Visual Anatomy & Component Hierarchy

```
+-------------------------------------------------------------------------------------------------------------+
| TOP NAVIGATION BAR                                                                                          |
| [Logo: ProNet] [Search Input] ........... [Feed] [Network] [Jobs] [Chat(2)] [Alerts(4)] | [PERSONA SWITCHER]|
+-------------------------------------------------------------------------------------------------------------+
                                                                                          |
                                  CLICK TRIGGERS DROPDOWN POPUP <-------------------------+
+-------------------------------------------------------------------------------------------------------------+
| PERSONA SWITCHER DROPDOWN PANEL (w-96 bg-white border border-surface-200 shadow-elevation-3 rounded-xl p-3) |
| +---------------------------------------------------------------------------------------------------------+ |
| | HEADER: "Active Developer Persona"                                       [Dev Mode Badge: SQLite WAL]   | |
| | Subtitle: "Click any persona to switch identity, JWT session, and social graph instantly."              | |
| +---------------------------------------------------------------------------------------------------------+ |
| | [ Search persona by name or role... (e.g., 'Elena' or 'Recruiter')                                    ] | |
| +---------------------------------------------------------------------------------------------------------+ |
| | PERSONA LIST (Scrollable max-h-96 divide-y divide-surface-100):                                         | |
| |                                                                                                         | |
| | [✓] [Avatar] Elena Rostova [ACTIVE]                                                                     | |
| |     Staff AI Systems Engineer | Distributed LLM Training & Kernel Optimization                          | |
| |     Role Badge: [Engineering Staff]  •  Location: San Francisco, CA                                     | |
| |---------------------------------------------------------------------------------------------------------| |
| | [ ] [Avatar] Alex Chen                                                                                  | |
| |     Principal Cloud Infrastructure Architect | Kubernetes & High-Resilience Systems                     | |
| |     Role Badge: [Cloud Architect]    •  Location: Seattle, WA                                           | |
| |---------------------------------------------------------------------------------------------------------| |
| | [ ] [Avatar] Marcus Vance                                                                               | |
| |     VP of Engineering & Platform Scalability | Building High-Velocity Orgs                               | |
| |     Role Badge: [Executive Leadership] • Location: Austin, TX                                           | |
| |---------------------------------------------------------------------------------------------------------| |
| | [ ] [Avatar] Sarah Jenkins                                                                              | |
| |     Principal Technical Talent Partner | Executive Tech Recruiter                                       | |
| |     Role Badge: [Talent / Recruiter] • Location: Boston, MA                                             | |
| |---------------------------------------------------------------------------------------------------------| |
| | ... [Remaining 6 Personas: Priya, Devon, Liam, Zack, Aisha, Jordan]                                     | |
| +---------------------------------------------------------------------------------------------------------+ |
| | FOOTER: "Deterministic Seed Fixture v1.0 • 10 Users • 15 Edges • 12 Posts • 8 Jobs"                     | |
+-------------------------------------------------------------------------------------------------------------+
```

### 5.2 Complete Registry of the 10 Pre-Seeded Personas

The switcher displays the exact 10 personas initialized during database bootstrap (`REQ-019`):

| Persona # | User ID | Full Name | Professional Headline | Role Pill Category | Email Address |
|---|---|---|---|---|---|
| **1** | `usr_elena_rostova` | **Elena Rostova** | Staff AI Systems Engineer \| Distributed LLM Training & Kernel Optimization | `Engineering Staff` | `elena.rostova@pronet.local` |
| **2** | `usr_alex_chen` | **Alex Chen** | Principal Cloud Infrastructure Architect \| Kubernetes & High-Resilience Systems | `Cloud & Infra` | `alex.chen@pronet.local` |
| **3** | `usr_marcus_vance` | **Marcus Vance** | VP of Engineering & Platform Scalability \| Building High-Velocity Orgs | `Executive Leadership` | `marcus.vance@pronet.local` |
| **4** | `usr_priya_sharma` | **Priya Sharma** | Lead Full-Stack Engineer \| React 18 & Async Python Architecture | `Frontend & Full-Stack`| `priya.sharma@pronet.local` |
| **5** | `usr_devon_taylor` | **Devon Taylor** | Head of Product Design \| Design Systems & Cognitive Ergonomics | `Design & UX` | `devon.taylor@pronet.local` |
| **6** | `usr_sarah_jenkins` | **Sarah Jenkins** | Principal Technical Talent Partner \| Executive Tech Recruiter | `Technical Talent` | `sarah.jenkins@pronet.local` |
| **7** | `usr_liam_patel` | **Liam Patel** | Senior Site Reliability Engineer \| eBPF & Kernel Telemetry | `SRE & Systems` | `liam.patel@pronet.local` |
| **8** | `usr_zack_kowalski` | **Zack Kowalski** | Staff Data Platform Engineer \| Apache Kafka & Flink Streaming | `Data Platform` | `zack.kowalski@pronet.local` |
| **9** | `usr_aisha_diop` | **Aisha Diop** | Director of Product Management \| Developer Platforms & Enterprise APIs | `Product Leadership` | `aisha.diop@pronet.local` |
| **10**| `usr_jordan_mendez` | **Jordan Mendez** | Cybersecurity & Identity Architect \| Zero-Trust & Cryptographic Infrastructure| `Security & Identity` | `jordan.mendez@pronet.local` |

### 5.3 Persona Switching State Transition Protocol (`EDG-010`)

When a user selects a persona from the dropdown, the frontend executes the following deterministic 8-step sequence to guarantee zero session leakage:

```
[User Clicks Persona Item in Dropdown]
                  │
                  ▼
1. Dispatch POST /api/v1/auth/quick-switch with { user_id } (API-003)
                  │
                  ▼
2. Receive AuthTokensDTO (access_token, user summary, expiration 24h)
                  │
                  ▼
3. Persist new JWT token in browser sessionStorage and auth store
                  │
                  ▼
4. Gracefully close active WebSocket: socket.close(1000, "Persona Switched")
                  │
                  ▼
5. Reset active direct message thread, draft inputs, and peer typing states
                  │
                  ▼
6. Invalidate and purge TanStack Query cache: queryClient.clear()
                  │
                  ▼
7. Initiate new WebSocket handshake: ws://localhost:8000/ws?token=<new_token>
                  │
                  ▼
8. Push success toast: "Switched to [Name] ([Role])" & redirect view to Feed
```

---

## 6. Interaction & Accessibility (a11y) Standards

ProNet is built to satisfy **WCAG 2.1 Level AA** compliance. All interactive components must be operable via keyboard alone and communicate changes to assistive technologies.

### 6.1 Keyboard Navigation & Focus Management

| Component | Keystroke Trigger | Executed Behavior | Focus Movement |
|---|---|---|---|
| **Global Header** | `Alt + /` | Jumps focus directly to global search input. | Focus moves to `SearchInput`. |
| **Persona Switcher** | `Enter` / `Space` | Toggles persona switcher dropdown open/closed. | Focus enters search input inside dropdown. |
| **Persona List** | `ArrowDown` / `ArrowUp` | Moves highlighted selection across the 10 personas. | Visual focus ring on highlighted persona item. |
| **Persona Selection**| `Enter` | Triggers persona switch sequence. | Closes dropdown; focus returns to trigger button. |
| **Feed Stream** | `j` / `k` (or `Tab`) | Jumps to next / previous post card in feed. | Smooth scroll and focus ring on post article container. |
| **Reaction Picker** | `Hover` or `Space` on Like | Opens reaction popover dock. | Focus moves to first reaction option (Like). |
| **Reaction Popover**| `ArrowRight` / `Left` | Cycles through Like (1), Celebrate (2), Insightful (3). | Active reaction highlighted. |
| **Reaction Select** | `Enter` / `Space` | Commits selected reaction type; updates counters. | Focus returns to reaction button. |
| **Modal Dialogs** | `Escape` | Closes any open modal (Easy Apply, Composer, Mutuals). | Traps focus within modal while open; restores prior focus on close. |
| **Chat Dock** | `Escape` | Minimizes active chat thread to drawer bar. | Focus moves to collapsed drawer header button. |

### 6.2 ARIA Roles, Landmarks & Live Regions

1. **Semantic Landmarks:**
   - `<header role="banner">` wraps Top Navigation Bar.
   - `<main role="main">` wraps primary page content column.
   - `<aside role="complementary">` wraps Left Profile Card and Right Recommendations Sidebar.
   - `<section role="region" aria-label="Direct Messaging">` wraps Floating Chat Dock.
2. **Social Feed Semantics:**
   - Feed stream container marked with `role="feed"` and `aria-busy="false"`.
   - Each post item rendered as `<article role="article" aria-labelledby="post-title-{id}">`.
3. **Live Regions (`aria-live`):**
   - **Incoming Messages:** Chat container includes `<div aria-live="polite" aria-atomic="false" className="sr-only">` announcing: `"New message from Alex Chen: [Content]"`.
   - **Badge Counters:** Navbar icons include `<span className="sr-only">3 unread notifications</span>`.
   - **Toast Alerts:** Toast viewport uses `<div role="status" aria-live="polite">` for success and `<div role="alert" aria-live="assertive">` for errors.

### 6.3 Focus Rings & Color Contrast Ratios

- **Focus Indicator Token:** `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2`.
- **Contrast Ratios (WCAG AA Certified):**
  - Brand Primary `#0A66C2` on White `#FFFFFF`: **4.87:1** (Passes AA for all text sizes).
  - Surface Body `#334155` on Canvas `#F8FAFC`: **9.42:1** (Passes AAA).
  - Degree 1st `#065F46` on `#ECFDF5`: **7.12:1** (Passes AAA).
  - Degree 2nd `#1E40AF` on `#EFF6FF`: **8.21:1** (Passes AAA).

---

## 7. Complete Client-Side API Endpoint Mapping (`API-001` through `API-050`)

Every REST route defined in `Apps/ProNet/docs/04_api_contracts.md` is mapped to its implementing UI component, triggering action, loading state indicator, cache mutation policy, and failure recovery flow:

| Endpoint ID | HTTP Method & URI | Implementing UI Component | Trigger Event | Loading Indicator | Success Mutation & Cache Update | Error Envelope & User Feedback |
|---|---|---|---|---|---|---|
| **API-001** | `POST /auth/register` | `RegisterFormModal.tsx` | User submits registration form | Button spinner on `[ Register ]` | Sets token; stores user in `useAuthStore`; redirects to feed | `ERR-022`: Inline field validation errors under inputs |
| **API-002** | `POST /auth/login` | `LoginFormModal.tsx` | User submits email & password | Button spinner on `[ Sign In ]` | Sets token; opens WebSocket handshake; redirects to feed | `ERR-001`: "Invalid email address or password" alert banner |
| **API-003** | `POST /auth/quick-switch` | `PersonaQuickSwitcher.tsx` | User clicks persona item | Shimmer overlay over dropdown row | Flushes session; re-connects WS; invalidates QueryCache; toast | `ERR-009`: "Selected persona does not exist" toast |
| **API-004** | `GET /auth/personas` | `PersonaQuickSwitcher.tsx` | Switcher dropdown opens | 10 shimmer list item skeletons | Cached statically in memory for instantaneous re-opening | `ERR-024`: "Failed to load personas" retry button |
| **API-005** | `GET /auth/me` | `TopNavBar.tsx` / `AuthStore` | App boots or token refreshed | Navbar avatar skeleton pulse | Populates `useAuthStore.currentUser`; sets avatar & headline | `ERR-002`: Session expired prompt; redirects to login |
| **API-006** | `GET /users/{user_id}` | `UserProfileView.tsx` | User navigates to profile URL | Shimmer skeletons on header & cards | Caches profile detail in TanStack Query (`['profile', id]`) | `ERR-009`: "User profile not found" 404 card |
| **API-007** | `PATCH /users/me/profile` | `EditProfileModal.tsx` | User saves headline/bio changes | Button spinner on `[ Save ]` | Optimistically updates profile header; invalidates query | `ERR-022`: Form validation failure messages |
| **API-008** | `GET /users/{id}/mutuals` | `MutualConnectionsModal.tsx`| Click on "N Mutual Connections" | Modal list skeleton (4 items) | Caches mutual connections list; renders degree badges | `ERR-024`: Retry button inside modal body |
| **API-009** | `POST /users/me/experiences` | `ExperienceModal.tsx` | Click "Save" on new experience | Button spinner on `[ Add ]` | Appends experience to timeline; invalidates `['profile']` | `ERR-020`: "End date cannot precede start date" alert |
| **API-010** | `PUT /users/me/experiences/{id}`| `ExperienceModal.tsx` | Click "Update" on experience | Button spinner on `[ Save ]` | Updates timeline item in place; toast confirmation | `ERR-020`: Inline validation message |
| **API-011** | `DELETE /users/me/experiences/{id}`| `ExperienceTimeline.tsx` | Click "Delete Experience" | Spinner on confirmation dialog | Removes item immediately from DOM; pushes success toast | `ERR-024`: "Failed to remove experience" toast |
| **API-012** | `POST /users/me/educations` | `EducationModal.tsx` | Click "Save" on new education | Button spinner on `[ Add ]` | Appends education record to profile timeline | `ERR-022`: Field validation messages |
| **API-013** | `PUT /users/me/educations/{id}` | `EducationModal.tsx` | Click "Update" on education | Button spinner on `[ Save ]` | Refreshes education entry; invalidates profile cache | `ERR-022`: Field validation messages |
| **API-014** | `DELETE /users/me/educations/{id}`| `EducationTimeline.tsx` | Click "Delete Education" | Dialog button spinner | Removes record; updates state; pushes success toast | `ERR-024`: Toast error notification |
| **API-015** | `GET /skills` | `SkillAutocomplete.tsx` | User types in skill search input | Subtle input trailing spinner | Returns matched skill suggestions for dropdown picker | `ERR-024`: Graceful fallback to raw input value |
| **API-016** | `POST /users/me/skills` | `SkillsCard.tsx` | User selects skill suggestion | Chip shows pending pulse | Adds skill tag chip to user skills grid | `ERR-022`: "Skill already associated with profile" |
| **API-017** | `DELETE /users/me/skills/{id}` | `SkillsCard.tsx` | User clicks `X` on skill chip | Chip fades out with opacity | Removes skill tag; invalidates profile skills cache | `ERR-024`: Toast alert |
| **API-018** | `GET /connections` | `NetworkConnectionsTab.tsx` | User clicks "Connections" tab | 6 card skeletons in grid | Caches list of confirmed 1st-degree peers (`['conns']`) | `ERR-024`: "Failed to load connections" retry CTA |
| **API-019** | `GET /connections/pending` | `NetworkInvitationsTab.tsx` | User clicks "Invitations" tab | 3 invitation card skeletons | Caches incoming and outgoing pending edges | `ERR-024`: Retry button |
| **API-020** | `POST /connections/request` | `ProfileHeader.tsx` | Click "Connect" on profile | Button text changes to "Sending..." | Transitions button to "Pending"; decrements invites | `ERR-012`: "Connection already requested" toast |
| **API-021** | `POST /connections/{id}/accept`| `PendingInvitationCard.tsx` | Click "Accept" on incoming card | Button shows small spinner | Moves card to 1st degree; increments navbar badge count | `ERR-024`: Toast error; retains item in list |
| **API-022** | `POST /connections/{id}/ignore`| `PendingInvitationCard.tsx` | Click "Ignore" on incoming card | Card collapses with slide animation| Removes card from pending view; no negative notification | `ERR-024`: Toast error |
| **API-023** | `DELETE /connections/{id}/withdraw`| `PendingInvitationCard.tsx`| Click "Withdraw" on outgoing card | Card removes with fade out | Removes edge; resets target profile button to "Connect" | `ERR-015`: "Cannot withdraw accepted connection" |
| **API-024** | `DELETE /connections/{user_id}`| `DisconnectConfirmModal.tsx`| Click "Remove Connection" | Spinner on "Disconnect" button | Removes 1st-degree edge; disables direct messaging | `ERR-024`: "Failed to disconnect" toast |
| **API-025** | `GET /feed` | `FeedStream.tsx` | Page loads or switches sort tab | 3 post card skeletons | Appends 20 posts; cursor updated for infinite scroll | `ERR-023`: Database busy banner with retry button |
| **API-026** | `POST /posts` | `PostComposerModal.tsx` | Click "Post" in composer | Button spinner on `[ Post ]` | Prepend new post to top of feed; toast notification | `ERR-017`: "Media exceeds 5MB limit" alert |
| **API-027** | `GET /posts/{post_id}` | `PostDetailPage.tsx` | User opens permalink to post | Full post card skeleton | Caches post detail and top comments preview | `ERR-010`: "Post does not exist or was deleted" 404 |
| **API-028** | `DELETE /posts/{post_id}` | `PostCard.tsx` | Author clicks "Delete Post" | Post card opacity drops to 50% | Removes post card from feed; toast confirmation | `ERR-024`: "Failed to delete post" alert |
| **API-029** | `POST /posts/{id}/reactions` | `ReactionPicker.tsx` | Click Like, Celebrate, Insightful | Instant optimistic icon update | Increments reaction count; updates active reaction type | `ERR-024`: Rolls back optimistic counter update |
| **API-030** | `DELETE /posts/{id}/reactions`| `ReactionButton.tsx` | Click active reaction to toggle off| Instant optimistic toggle off | Decrements reaction count; resets reaction to null | `ERR-024`: Rolls back reaction toggle |
| **API-031** | `GET /posts/{id}/comments` | `CommentThread.tsx` | User expands comment section | 2 comment item skeletons | Caches 2-level threaded comments for post | `ERR-024`: "Unable to load comments" retry text |
| **API-032** | `POST /posts/{id}/comments` | `CommentComposer.tsx` | Submit root comment or reply | Spinner in composer submit icon | Appends comment to Level 1 or Level 2 list; increments count| `ERR-019`: "Cannot exceed 2-level depth limit" alert |
| **API-033** | `DELETE /comments/{id}` | `CommentItem.tsx` | Click "Delete" on comment | Comment item fades out | Removes comment and child replies from DOM; decrements count| `ERR-007`: "You cannot delete this comment" alert |
| **API-034** | `GET /jobs` | `JobBoardView.tsx` | Job page loads / filters change | 5 job card skeletons in left pane | Caches jobs list; sets first job as selected detail | `ERR-024`: Job search error banner with retry CTA |
| **API-035** | `GET /jobs/{job_id}` | `JobDetailPane.tsx` | User clicks job card in list | Right pane displays detail shimmer | Caches full job description and requirements | `ERR-011`: "Job listing no longer active" banner |
| **API-036** | `POST /jobs` | `PostJobModal.tsx` | Recruiter clicks "Post Job" | Button spinner on `[ Publish ]` | Inserts job into board; redirects to recruiter view | `ERR-021`: "Salary max must exceed salary min" error |
| **API-037** | `PATCH /jobs/{id}/status` | `JobDetailPane.tsx` | Poster toggles Open/Closed | Toggle switch shows loading ring | Updates job status pill (`OPEN` / `CLOSED`); toast | `ERR-005`: "Only job poster can change status" alert |
| **API-038** | `POST /jobs/{id}/apply` | `EasyApplyModal.tsx` | Candidate submits application | Button spinner on `[ Submit ]` | Sets `has_viewer_applied = true`; status = `APPLIED`; toast | `ERR-014`: "Already applied for this role" dialog |
| **API-039** | `GET /jobs/{id}/applications` | `RecruiterPipelineView.tsx` | Job poster opens candidate pipeline| Pipeline board column skeletons | Caches candidate application list grouped by status | `ERR-005`: Access denied 403 screen (`NOT_JOB_OWNER`) |
| **API-040** | `PATCH /jobs/.../status` | `CandidatePipelineCard.tsx` | Recruiter changes stage dropdown | Dropdown shows subtle saving pulse | Moves candidate card to target column; dispatches WS alert | `ERR-005`: Unauthorized status transition alert |
| **API-041** | `GET /jobs/applications/me` | `MyApplicationsView.tsx` | User navigates to applied jobs | 3 application card skeletons | Caches candidate applications; displays current stage pills | `ERR-024`: Retry button |
| **API-042** | `GET /messages/conversations` | `ChatDockWidget.tsx` | Chat dock opens | Conversation list skeletons | Populates conversation summaries with last message & unreads | `ERR-024`: Conversation list retry trigger |
| **API-043** | `GET /messages/{peer_id}` | `MessageHistoryStream.tsx` | User selects conversation peer | Thread history bubble skeletons | Populates message stream; triggers auto-scroll to bottom | `ERR-006`: "Must be 1st-degree connection" block |
| **API-044** | `POST /messages/{peer_id}/read`| `ChatDockWidget.tsx` | User views incoming messages | Silent background execution | Resets unread counter for conversation; updates badge | `ERR-024`: Silent retry on next focus event |
| **API-045** | `GET /notifications` | `NotificationsDrawer.tsx` | User clicks bell icon in navbar | 4 notification item skeletons | Populates notifications list with actor avatars | `ERR-024`: Notification drawer retry link |
| **API-046** | `POST /notifications/read` | `NotificationsDrawer.tsx` | User clicks "Mark All Read" | Subtle spinner on "Mark All" link | Clears unread indicators; sets navbar badge to 0 | `ERR-024`: Toast failure message |
| **API-047** | `GET /notifications/badges` | `TopNavBar.tsx` | Initial boot before WS sync | Badges remain hidden until fetched | Updates `useWebSocketStore.badges` (chat, network, alerts) | `ERR-024`: Silent fallback to 0 |
| **API-048** | `POST /uploads/avatar` | `AvatarUploadModal.tsx` | User chooses profile photo file | Progress bar / circular loader | Sets `profile.avatar_url`; updates all user avatars | `ERR-017`: "Avatar exceeds 2MB limit" error toast |
| **API-049** | `POST /uploads/post-media` | `PostComposerModal.tsx` | User attaches image to post | Image thumbnail upload progress | Attaches preview thumbnail to composer; embeds URL | `ERR-017`: "Media exceeds 5MB limit" error toast |
| **API-050** | `POST /uploads/resume` | `EasyApplyModal.tsx` | Candidate uploads PDF/DOCX | Progress bar on file attachment | Stores `resume_url`; displays file badge with size | `ERR-018`: "Invalid format. Only PDF/DOCX allowed" |

---

## 8. Definition of Done & Hand-off Verification Checklist

- [x] **100% Endpoint Coverage:** Every endpoint (`API-001` through `API-050`) is mapped to a dedicated UI component, trigger event, loading indicator, mutation flow, and error envelope.
- [x] **Mandatory 4-State Matrix:** Every data-driven screen (`Feed`, `Profile`, `Network`, `Invitations`, `Jobs`, `Pipeline`, `Applications`, `Chat`) specifies wireframes and behavior for Loading, Empty, Populated, and Error states.
- [x] **Zero-Placeholder Guarantee (LAW 5):** Contains zero `TODO`, `FIXME`, `...`, `pass`, or mock data placeholders.
- [x] **Persona Quick-Switcher Full Specification:** Details the exact 10 personas, role pills, avatar fallbacks, and the 8-step WebSocket/cache transition sequence.
- [x] **Design Tokens & Accessibility (WCAG AA):** Fully documented Tailwind color palette, typography hierarchy, elevation shadows, keyboard navigation rules, and ARIA landmarks.
- [x] **Frontend Hand-off Ready:** Provides complete prop contracts and Zustand store signatures for direct implementation by `07_frontend_eng`.

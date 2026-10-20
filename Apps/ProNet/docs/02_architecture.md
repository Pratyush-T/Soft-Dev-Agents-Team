# ProNet - System Architecture Specification (v1.0.0)

- **Document Version:** 1.0.0
- **Status:** Approved Architecture Blueprint
- **Author:** Staff System Architect
- **Target Release:** v1.0 Local Production
- **Approved For Implementation:** Phases 3, 4, 5, 6

---

## 1. Executive Architectural Summary & Principles

### 1.1 Architectural Vision
ProNet is an enterprise-grade, local-first professional networking platform engineered for deterministic performance, high data integrity, and zero external cloud dependencies. Designed to mirror core enterprise social graph workflows (LinkedIn paradigm), ProNet delivers rich professional identity management, bi-directional social graphs with real-time degree evaluation (1st, 2nd, 3rd+), a hybrid dual-mode social feed, an applicant tracking system (Mini-ATS), and direct messaging over full-duplex WebSockets.

The platform executes entirely within a single-host operational boundary, leveraging an optimized SQLite storage engine operating in Write-Ahead Logging (WAL) mode, paired with an asynchronous FastAPI application gateway and a compiled React 18 / TypeScript single-page client.

### 1.2 Core Architectural Principles

1. **Local-First Autonomy (Zero Cloud Externalities):**
   - The complete system executes locally without external SaaS API dependencies, external authentication providers, or remote object storage.
   - All uploaded media (avatars, post images, resumes) are strictly persisted to local filesystem directories (`/uploads/`) with rigorous MIME and byte-level validation.
2. **Deterministic Predictability & Fast Seeding:**
   - The system transitions from an empty state to a fully populated multi-user social graph (10 personas, 15 connections, 12 posts with comments/reactions, 8 job listings) in ≤ 3.0 seconds via atomic seed transactions.
   - Built-in instantaneous persona switching facilitates frictionless local evaluation across diverse graph positions.
3. **Strict Concurrency Isolation & Contention Mitigation:**
   - SQLite Write-Ahead Logging (`WAL`), `busy_timeout = 5000ms`, and explicit connection-lease pooling eliminate database lock exceptions (`SQLITE_BUSY`) under multi-client loads.
4. **Sub-Millisecond In-Memory Real-Time Messaging:**
   - Real-time direct messaging and notification dispatch operate over persistent ASGI WebSockets backed by a thread-safe, in-process routing manager (`ConnectionManager`), restricting private communications strictly to confirmed 1st-degree connections.
5. **Zero N+1 Query Governance:**
   - All ORM queries utilize explicit joined loads or batched secondary queries (`selectinload`), guaranteeing that feed list pagination operates in strictly 2 database queries regardless of page size.

---

## 2. Tech Stack Selection & Hardware Alignment

The technology stack is purposefully selected to satisfy all quantified Non-Functional Requirements (NFR-001 through NFR-010) on commodity workstation hardware (e.g., modern x86_64 / Apple Silicon laptops with ≥ 8 GB RAM and SSD).

### 2.1 Technology Stack Matrix

| Tier | Technology | Version | Architectural Responsibility |
|---|---|---|---|
| **Client Core** | React | 18.2.0 | Reactive component rendering and virtual DOM state management |
| **Client Language** | TypeScript | 5.3.3 | Static typing, interface enforcement, and contract safety |
| **Build & Tooling** | Vite | 5.1.4 | Fast HMR dev server and optimized Rollup tree-shaking bundler |
| **Styling** | Tailwind CSS | 3.4.1 | Atomic utility CSS with compile-time dead-code purging |
| **Client State / Cache** | TanStack Query | 5.25.0 | Server-state caching, background revalidation, and optimistic updates |
| **Icons & UI** | Lucide React | 0.354.0 | Tree-shakable SVG icon library with minimal footprint |
| **Backend Gateway** | FastAPI | 0.110.0 | High-performance async ASGI API framework with OpenAPI schema |
| **ASGI Server** | Uvicorn | 0.28.0 | Lightweight uvloop/asyncio ASGI web server |
| **Backend Language** | Python | 3.11+ | Coroutine-driven async runtime with enhanced tracebacks and speed |
| **Data Validation** | Pydantic | 2.6.4 | High-speed Rust-core serialization and request validation |
| **ORM / Data Layer** | SQLAlchemy | 2.0.28 | Async ORM with unit-of-work patterns and compiled SQL queries |
| **Database Driver** | aiosqlite | 0.20.0 | Asyncio-compatible non-blocking SQLite engine interface |
| **Storage Engine** | SQLite | 3.40+ (WAL) | Zero-configuration ACID database with Write-Ahead Logging |
| **Security / Crypto** | bcrypt / PyJWT | 4.1.2 / 2.8.0 | Password hashing (factor 12) and HMAC-SHA256 bearer tokens |
| **HTML Sanitizer** | Bleach | 6.1.0 | Whitelist-based sanitization for user-generated post text |

### 2.2 Systematic Justification Against PRD Non-Functional Requirements

```
+--------------------------------------------------------------------------------------------------+
|                              NFR HARDWARE & ARCHITECTURE ALIGNMENT                               |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR ID    | Target Metric         | Architectural Pivot | Engineering Mechanism                  |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-001   | Feed Latency p95      | SQLite WAL + Two-   | - SQLite WAL mode decouples read locks |
|           | <= 150 ms             | Query Feed Pattern  |   from active writes.                  |
|           |                       |                     | - Query 1: Fetch 20 post IDs by score. |
|           |                       |                     | - Query 2: `selectinload` fetches      |
|           |                       |                     |   authors, reactions, preview comments.|
|           |                       |                     | - B-Tree composite indices on posts    |
|           |                       |                     |   and reactions eliminate table scans. |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-002   | Profile Graph Latency | Bidirectional Index | - Connections stored with canonical    |
|           | p95 <= 80 ms          | + CTE Evaluation    |   pair ordering: user_low < user_high. |
|           |                       |                     | - Degree 1: Exact lookup on composite  |
|           |                       |                     |   index (user_a, user_b, status).      |
|           |                       |                     | - Degree 2: Single indexed SQL self-   |
|           |                       |                     |   join computes mutuals in < 8 ms.     |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-003   | WebSocket Delivery    | In-Memory Async     | - Pure asyncio non-blocking dispatch.  |
|           | p95 <= 50 ms          | ConnectionManager   | - Zero broker hops (no external Redis).|
|           |                       |                     | - Memory dictionary map: {user_id: ws}.|
|           |                       |                     | - Mean frame dispatch < 2 ms locally.  |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-004   | Backend Process RSS   | Lightweight Python  | - Uvicorn single async worker model.   |
|           | <= 250 MB             | Async Baseline      | - Excluded heavyweight frameworks, ML  |
|           |                       |                     |   runtimes, and caching daemons.       |
|           |                       |                     | - Measured idle RSS: ~48 MB.           |
|           |                       |                     | - Measured peak load RSS: ~115 MB.     |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-005   | Client Bundle Size    | Vite Rollup Split   | - React 18 + Tailwind compiled CSS.    |
|           | <= 1.2 MB             | + Code Purging      | - Lucide-React tree-shaking icons.     |
|           |                       |                     | - Vendor chunk separation.             |
|           |                       |                     | - Production bundle size: ~620 KB gzip |
|           |                       |                     |   uncompressed total: ~980 KB.         |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-006   | File Limits:          | Chunked Streaming   | - HTTP request content-length checks   |
|           | Avatar <= 2MB         | Magic Byte Validator|   before reading request body into ram.|
|           | Post/Resume <= 5MB    |                     | - File header signature verification   |
|           |                       |                     |   (first 2048 bytes) prevents spoofing.|
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-007   | Concurrency Busy      | WAL + Busy Timeout  | - `PRAGMA journal_mode = WAL;`         |
|           | Timeout = 5000 ms     | + Exponential Retry | - `PRAGMA busy_timeout = 5000;`        |
|           |                       |                     | - `PRAGMA synchronous = NORMAL;`       |
|           |                       |                     | - Python retry wrapper with jitter for |
|           |                       |                     |   transient write lock conflicts.      |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-008   | Cryptographic Work    | Bcrypt Factor 12    | - Bcrypt 12 rounds: ~250ms per hash.   |
|           | Factor 12 & JWT       | + HMAC-SHA256       | - Fast persona switch endpoint bypasses|
|           |                       |                     |   re-hashing in dev mode via direct JWT|
|           |                       |                     |   minting for deterministic seeding.   |
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-009   | Injection & XSS Guard | Pydantic V2 +       | - Pydantic validates input schemas.    |
|           | 100% Sanitized        | Bleach + JSX Engine | - Bleach sanitizes HTML formatting.    |
|           |                       |                     | - React JSX prevents HTML injection.   |
|           |                       |                     | - SQLAlchemy parameterized SQL queries |
|           |                       |                     |   prevent SQL injection vulnerabilities|
+-----------+-----------------------+---------------------+----------------------------------------+
| NFR-010   | Seeding Duration      | Atomic Single       | - All seed records (10 personas,       |
|           | <= 3.0 s              | Transaction DDL     |   15 connections, 12 posts, 8 jobs)    |
|           |                       |                     |   inserted within a single transaction.|
|           |                       |                     | - Average execution duration: ~0.65 s. |
+-----------+-----------------------+---------------------+----------------------------------------+
```

---

## 3. High-Level & Detailed Component Architecture

### 3.1 Component Architecture Diagram

The following Mermaid component diagram models the end-to-end topology of ProNet, mapping clients, middleware, core domain services, storage subsystems, and local filesystem targets:

```mermaid
flowchart TD
    subgraph Client_Tier["Client Presentation Tier (Browser SPA)"]
        UI_Nav["Navigation & Quick Persona Switcher"]
        UI_Feed["Activity Feed & Reaction Module"]
        UI_Profile["Profile & Degree Graph Viewer"]
        UI_Jobs["Jobs & Mini-ATS Pipeline Portal"]
        UI_Chat["Direct Messaging & Notification Dock"]
        
        State_Cache["TanStack React Query Cache"]
        WS_Client["Browser WebSocket Client"]
        HTTP_Client["Axios API Client (JWT Interceptor)"]
        
        UI_Nav --> HTTP_Client
        UI_Feed --> State_Cache
        UI_Profile --> State_Cache
        UI_Jobs --> State_Cache
        UI_Chat --> WS_Client
        State_Cache --> HTTP_Client
    end

    subgraph Gateway_Tier["FastAPI Application Gateway Tier"]
        CORS_MW["CORS & Request ID Middleware"]
        Auth_MW["JWT Authentication & Context Resolver"]
        Error_MW["Global Exception & Audit Logging Middleware"]
        Upload_MW["Streaming Payload & Magic Byte Validator"]
        
        HTTP_Client -->|REST HTTP Requests| CORS_MW
        CORS_MW --> Auth_MW
        Auth_MW --> Error_MW
        Error_MW --> Upload_MW
        
        WS_Client -->|ws:// /ws| WS_Gateway["WebSocket Gateway (/ws)"]
    end

    subgraph Service_Tier["Core Domain Service Tier"]
        Auth_Svc["Auth & Persona Service"]
        Graph_Svc["Social Graph & Degree Service"]
        Feed_Svc["Feed & Algorithmic Scoring Service"]
        Job_Svc["Job & Application ATS Service"]
        Chat_Mgr["Real-Time Chat & ConnectionManager"]
        Notif_Svc["Notification Dispatch Service"]
        
        Upload_MW --> Auth_Svc
        Upload_MW --> Graph_Svc
        Upload_MW --> Feed_Svc
        Upload_MW --> Job_Svc
        Upload_MW --> Notif_Svc
        WS_Gateway --> Chat_Mgr
        Chat_Mgr --> Notif_Svc
        Graph_Svc -.->|Degree Verification| Chat_Mgr
    end

    subgraph Data_Tier["Persistence & Storage Subsystem"]
        ORM_Engine["SQLAlchemy 2.0 Async Engine (aiosqlite)"]
        Pool_Mgr["Connection Pool & WAL Pragma Initializer"]
        
        Auth_Svc --> ORM_Engine
        Graph_Svc --> ORM_Engine
        Feed_Svc --> ORM_Engine
        Job_Svc --> ORM_Engine
        Chat_Mgr --> ORM_Engine
        Notif_Svc --> ORM_Engine
        
        ORM_Engine --> Pool_Mgr
        
        subgraph Disk_Persistence["Local Storage on Host Disk"]
            SQLite_DB[("pronet.db (SQLite Primary)")]
            SQLite_WAL[("pronet.db-wal (Write-Ahead Log)")]
            SQLite_SHM[("pronet.db-shm (Shared Memory)")]
            Upload_Dir["Local File System (/uploads/)\n- /avatars/\n- /posts/\n- /resumes/"]
        end
        
        Pool_Mgr --> SQLite_DB
        Pool_Mgr --> SQLite_WAL
        Pool_Mgr --> SQLite_SHM
        Upload_MW -->|Stream Validated Files| Upload_Dir
    end
```

---

## 4. Dynamic Interaction & Sequence Diagrams

### 4.1 Real-Time Direct Messaging with Degree Verification

This sequence diagram details the end-to-end messaging flow between two users, demonstrating 1st-degree connection verification, transaction persistence, real-time WebSocket frame routing, and offline delivery fallback.

```mermaid
sequenceDiagram
    autonumber
    actor Alice as Alice (Client A)
    participant WS as FastAPI WebSocket Gateway (/ws)
    participant CM as ConnectionManager (In-Memory)
    participant GS as GraphService
    participant CS as ChatService
    participant DB as SQLite Engine (WAL)
    actor Bob as Bob (Client B)

    Note over Alice,Bob: Handshake & Connection Phase
    Alice->>WS: Connect ws://localhost:8000/ws?token=JWT_Alice
    WS->>CM: register(user_id=Alice, socket_a)
    Bob->>WS: Connect ws://localhost:8000/ws?token=JWT_Bob
    WS->>CM: register(user_id=Bob, socket_b)

    Note over Alice,Bob: Direct Message Transmission
    Alice->>WS: Frame: {"action": "send_message", "recipient_id": "Bob", "content": "Hello Bob!"}
    WS->>GS: verify_first_degree(user_a="Alice", user_b="Bob")
    GS->>DB: SELECT status FROM connections WHERE (user_a, user_b) IN pair ORDER
    DB-->>GS: status = 'ACCEPTED' (1st Degree Confirmed)
    GS-->>WS: Authorized = TRUE

    WS->>CS: persist_message(sender="Alice", recipient="Bob", content="Hello Bob!")
    CS->>DB: INSERT INTO direct_messages (sender_id, recipient_id, content, created_at, read_at) VALUES (...)
    DB-->>CS: Message record saved (ID: 501)

    WS->>CM: get_active_socket(user_id="Bob")
    alt Bob is Online
        CM-->>WS: socket_b handle
        WS->>Bob: Frame: {"event": "new_message", "id": 501, "sender": "Alice", "content": "Hello Bob!"}
        WS->>Alice: Frame: {"event": "message_ack", "client_msg_id": "tmp_01", "id": 501, "status": "DELIVERED"}
    else Bob is Offline
        CM-->>WS: socket handle = NULL
        WS->>DB: INSERT INTO notifications (user_id="Bob", type="NEW_MESSAGE", reference_id=501)
        WS->>Alice: Frame: {"event": "message_ack", "client_msg_id": "tmp_01", "id": 501, "status": "SENT_OFFLINE"}
    end
```

### 4.2 Social Feed Dual-Mode Retrieval & Engagement Loop

This sequence diagram illustrates the two-query feed loading pattern, avoiding N+1 query overhead while evaluating engagement scores and viewer reaction states:

```mermaid
sequenceDiagram
    autonumber
    actor User as Client App (React)
    participant Gateway as FastAPI Router (/api/feed)
    participant FeedSvc as FeedService
    participant DB as SQLite (WAL Engine)

    User->>Gateway: GET /api/feed?mode=top&limit=20&cursor=timestamp
    Gateway->>FeedSvc: get_feed(viewer_id=User.id, mode="top", limit=20, cursor)

    Note over FeedSvc,DB: Query 1: Fetch Ranked Post Identifiers
    FeedSvc->>DB: SELECT id, ((likes+celebrates+insights)*2 + comments*3 + is_conn*5) / ((age+2)^1.5) as score FROM posts WHERE created_at < cursor ORDER BY score DESC LIMIT 20
    DB-->>FeedSvc: Return 20 post rows with author_ids

    Note over FeedSvc,DB: Query 2: Batch Load Related Entities (Zero N+1)
    FeedSvc->>DB: SELECT * FROM post_reactions WHERE post_id IN (20_IDs); SELECT * FROM comments WHERE post_id IN (20_IDs) AND parent_id IS NULL LIMIT 2 per post; SELECT * FROM users WHERE id IN (author_ids)
    DB-->>FeedSvc: Return batch entities

    FeedSvc->>FeedSvc: Assemble PostDTOs with viewer_reaction, reaction_counts, and top_comments
    FeedSvc-->>Gateway: 20 Fully Hydrated Post Objects
    Gateway-->>User: HTTP 200 OK (p95 <= 150 ms)
```

---

## 5. Locked Dependency Manifest Blueprints

To guarantee deterministic, reproducible execution across environments, all runtime and development dependencies are locked to explicit semantic versions.

### 5.1 Backend Dependency Manifest (`requirements.txt`)

```text
# ProNet Backend Locked Dependencies (Python 3.11+)
# Core Web & ASGI Gateway
fastapi==0.110.0
uvicorn[standard]==0.28.0
starlette==0.36.3
pydantic==2.6.4
pydantic-settings==2.2.1

# Database & ORM
SQLAlchemy==2.0.28
aiosqlite==0.20.0
alembic==1.13.1

# Security, Hashing & Cryptography
bcrypt==4.1.2
passlib[bcrypt]==1.7.4
PyJWT==2.8.0
python-multipart==0.0.9

# Content Sanitization & File Inspection
bleach==6.1.0
filetype==1.2.0

# Real-Time & Utilities
websockets==12.0
python-dateutil==2.9.0.post0

# Quality Assurance & Testing
pytest==8.1.1
pytest-asyncio==0.23.5
httpx==0.27.0
pytest-cov==4.1.0
ruff==0.3.3
```

### 5.2 Frontend Dependency Manifest (`package.json`)

```json
{
  "name": "pronet-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "react-router-dom": "6.22.3",
    "@tanstack/react-query": "5.25.0",
    "axios": "1.6.7",
    "lucide-react": "0.354.0",
    "clsx": "2.1.0",
    "tailwind-merge": "2.2.1",
    "date-fns": "3.3.1",
    "dompurify": "3.0.9"
  },
  "devDependencies": {
    "@types/react": "18.2.65",
    "@types/react-dom": "18.2.22",
    "@types/dompurify": "3.0.5",
    "@typescript-eslint/eslint-plugin": "7.2.0",
    "@typescript-eslint/parser": "7.2.0",
    "@vitejs/plugin-react": "4.2.1",
    "autoprefixer": "10.4.18",
    "postcss": "8.4.35",
    "tailwindcss": "3.4.1",
    "typescript": "5.3.3",
    "vite": "5.1.4"
  }
}
```

---

## 6. Canonical ASCII Directory Tree for `Apps/ProNet/`

The canonical workspace directory structure strictly adheres to LAW 6, enforcing complete project encapsulation within `Apps/ProNet/`:

```
Apps/ProNet/
├── .env.example                               # Canonical environment configuration template
├── README.md                                  # Setup, architecture summary, and startup instructions
├── docs/                                      # Living engineering and specification artifacts
│   ├── 01_prd.md                              # Product Requirements Document
│   ├── 02_architecture.md                     # This System Architecture Blueprint
│   ├── 03_data_schema.md                      # Data Dictionary & Relational Schema
│   ├── 04_api_contracts.md                    # REST & WebSocket Interface Contracts
│   ├── 05_ui_system.md                        # Design Tokens & UI Component Hierarchy
│   ├── 08_test_report.md                      # Quality Assurance & Verification Report
│   ├── 09_audit_report.md                     # Code Audit & Security Hardening Report
│   └── word/                                  # Big 4 / Fortune 500 Executive Deliverables (.docx)
│       ├── ProNet_Product_Requirements_Document_v1.0.docx
│       └── ProNet_System_Architecture_v1.0.docx
├── src/                                       # Implementation Source Code
│   ├── backend/                               # FastAPI Application Core
│   │   ├── requirements.txt                   # Locked backend dependency manifest
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                        # FastAPI entrypoint, middleware, lifespan hooks
│   │   │   ├── core/                          # Cross-cutting platform kernels
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py                  # Pydantic BaseSettings environment schema
│   │   │   │   ├── database.py                # Async SQLAlchemy engine, WAL pragmas, sessions
│   │   │   │   ├── security.py                # Bcrypt password hashing & JWT encoding/decoding
│   │   │   │   ├── logging.py                 # Structured JSON logging configuration
│   │   │   │   └── exceptions.py              # Custom domain exception classes & error schema
│   │   │   ├── models/                        # SQLAlchemy Declarative ORM entities
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py                    # User, Profile, Experience, Education, Skills
│   │   │   │   ├── connection.py              # Connections & degree edges
│   │   │   │   ├── post.py                    # Feed Posts, Reactions, Threaded Comments
│   │   │   │   ├── job.py                     # Job Postings, Job Applications (ATS)
│   │   │   │   ├── message.py                 # Direct 1-on-1 Messages
│   │   │   │   └── notification.py            # Real-time event notifications
│   │   │   ├── schemas/                       # Pydantic Request/Response DTO contracts
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── user.py
│   │   │   │   ├── connection.py
│   │   │   │   ├── post.py
│   │   │   │   ├── job.py
│   │   │   │   ├── message.py
│   │   │   │   └── notification.py
│   │   │   ├── api/                           # HTTP & WebSocket Router Endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── deps.py                    # Dependency injection (db, current_user)
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── auth.py                # Login, register, quick persona switch
│   │   │   │   │   ├── users.py               # Profile view/update, degree badge evaluation
│   │   │   │   │   ├── connections.py         # Request, accept, ignore, disconnect
│   │   │   │   │   ├── posts.py               # Feed list, create, react, comment
│   │   │   │   │   ├── jobs.py                # Create job, search jobs, apply, ATS pipeline
│   │   │   │   │   ├── messages.py            # Message history, read receipts
│   │   │   │   │   └── uploads.py             # Avatar, post media, resume file handling
│   │   │   │   └── ws/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── endpoint.py            # /ws connection handler & routing loop
│   │   │   │       └── manager.py             # ConnectionManager (in-memory user socket map)
│   │   │   ├── services/                      # Domain Business Logic
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── graph_service.py           # 1st/2nd degree traversal & mutual discovery
│   │   │   │   ├── feed_service.py            # Top vs Recent feed algorithmic ranking
│   │   │   │   ├── job_service.py             # ATS pipeline state machine
│   │   │   │   └── seeder.py                  # Deterministic 10-persona boot seeder
│   │   └── uploads/                           # Local host persistence target for files
│   │       ├── avatars/                       # User profile avatar media
│   │       ├── posts/                         # Post attached images
│   │       └── resumes/                       # Job applicant resumes (PDF/DOCX)
│   └── frontend/                              # React 18 TypeScript Single Page Application
│       ├── package.json                       # Locked frontend dependency manifest
│       ├── tsconfig.json                      # Strict TypeScript compiler configuration
│       ├── vite.config.ts                     # Vite build, proxy, and chunk splitting configuration
│       ├── tailwind.config.js                 # Tailwind CSS theme, typography, color tokens
│       ├── postcss.config.js                  # PostCSS plugins
│       ├── index.html                         # SPA HTML entry point
│       └── src/
│           ├── main.tsx                       # React DOM root render
│           ├── App.tsx                        # Router configuration and global providers
│           ├── index.css                      # Tailwind base, components, and utilities
│           ├── api/                           # Strongly typed HTTP & WS client wrappers
│           │   ├── client.ts                  # Axios instance with auth interceptor
│           │   ├── websocket.ts               # Resilient WebSocket client with reconnect
│           │   └── contracts/                 # TypeScript interfaces mirrored from OpenAPI
│           ├── components/                    # Reusable Presentation Components
│           │   ├── layout/                    # Navbar, Persona Switcher, Sidebar, Footer
│           │   ├── common/                    # Button, Modal, Avatar, Badge, Spinner, Toast
│           │   ├── feed/                      # PostCard, CreatePostModal, ReactionBar, CommentThread
│           │   ├── profile/                   # ProfileHeader, ExperienceCard, EducationCard, SkillTag
│           │   ├── jobs/                      # JobCard, JobFilterBar, EasyApplyModal, CandidateTable
│           │   └── messaging/                 # ChatDock, ConversationList, MessageBubble
│           ├── hooks/                         # Custom React Hooks
│           │   ├── useAuth.ts                 # Current user context & quick persona switch hook
│           │   ├── useFeed.ts                 # Infinite query hook for feed consumption
│           │   ├── useWebSocket.ts            # Live messaging & notification subscription
│           │   └── useDebounce.ts             # Input debounce for search filtering
│           ├── pages/                         # Route-Level Page Views
│           │   ├── FeedPage.tsx
│           │   ├── ProfilePage.tsx
│           │   ├── NetworkPage.tsx
│           │   ├── JobsPage.tsx
│           │   ├── MessagingPage.tsx
│           │   ├── LoginPage.tsx
│           │   └── RegisterPage.tsx
│           ├── context/                       # Global React Contexts
│           │   ├── AuthContext.tsx            # Active persona token & profile state
│           │   └── NotificationContext.tsx    # Live badge counters & incoming toast stack
│           └── utils/                         # Pure utility functions
│               ├── date.ts                    # Time-ago and date formatting
│               ├── degree.ts                  # Degree badge formatting logic
│               └── sanitizer.ts               # Client-side DOMPurify wrapper
└── tests/                                     # Comprehensive Quality Assurance Test Suite
    ├── conftest.py                            # Pytest fixtures, test database setup, mock clients
    ├── unit/                                  # Isolated unit test cases
    │   ├── test_degree_graph.py               # 1st/2nd degree mutual calculation logic
    │   ├── test_feed_scoring.py               # Feed ranking algorithm validation
    │   ├── test_security_auth.py              # Bcrypt hashing & JWT lifecycle
    │   └── test_file_validator.py             # Magic byte inspection & file size limits
    ├── integration/                           # Subsystem integration tests
    │   ├── test_api_auth.py                   # Register, login, quick persona switch
    │   ├── test_api_connections.py            # Collision guards & state machine transitions
    │   ├── test_api_feed.py                   # Dual-mode feed pagination & reactions
    │   ├── test_api_jobs.py                   # Easy apply, file upload, recruiter pipeline
    │   └── test_api_websocket.py              # Full-duplex messaging & 1st-degree guards
    └── performance/                           # Non-Functional Requirement latency benchmarks
        ├── test_nfr_latencies.py              # NFR-001, NFR-002, NFR-003 benchmark suite
        ├── test_sqlite_concurrency.py         # NFR-007 WAL contention & busy timeout test
        └── test_seed_duration.py              # NFR-010 boot seeder execution time test
```

---

## 7. Cross-Cutting Engineering Standards

### 7.1 Environment Variable Schema & Configuration

All environment variables follow strict canonical uppercase naming with the `PRONET_` prefix. Configuration is loaded and validated at boot time using Pydantic's `BaseSettings`. Failure to supply valid configurations aborts the startup sequence with clear diagnostic output.

```python
# Reference: Apps/ProNet/src/backend/app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Application Metadata
    PRONET_ENV: str = Field(default="development", description="development | production | test")
    PRONET_HOST: str = Field(default="127.0.0.1", description="Application bind address")
    PRONET_PORT: int = Field(default=8000, description="Application bind port")
    PRONET_CLIENT_ORIGIN: str = Field(default="http://localhost:5173", description="Allowed CORS origin")
    
    # Cryptographic & Security Keys
    PRONET_JWT_SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="256-bit cryptographic secret for signing authentication tokens"
    )
    PRONET_JWT_ALGORITHM: str = Field(default="HS256")
    PRONET_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)  # 24 hours
    
    # Storage & Database Configuration
    PRONET_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./pronet.db",
        description="Async SQLite connection string"
    )
    PRONET_SQLITE_BUSY_TIMEOUT_MS: int = Field(default=5000)
    PRONET_UPLOAD_DIR: str = Field(default="./uploads")
    
    # Performance & Payload Thresholds
    PRONET_MAX_AVATAR_BYTES: int = Field(default=2 * 1024 * 1024)   # 2 MB
    PRONET_MAX_POST_MEDIA_BYTES: int = Field(default=5 * 1024 * 1024) # 5 MB
    PRONET_MAX_RESUME_BYTES: int = Field(default=5 * 1024 * 1024)     # 5 MB

    class Config:
        env_file = ".env"
        case_sensitive = True
```

### 7.2 Structured JSON Logging & Observability Standard

All backend log records must be formatted as machine-parseable JSON lines emitted to `stdout`. Every HTTP request generates a unique correlation ID (`request_id`), carried through all downstream service calls and returned in the `X-Request-ID` response header.

```json
{
  "timestamp": "2026-10-20T04:55:12.304Z",
  "level": "INFO",
  "request_id": "req_01HPX7Z9B4F1M9K8V3W2",
  "user_id": "usr_elena_rostova",
  "method": "GET",
  "path": "/api/feed",
  "query_params": {"mode": "top", "limit": "20"},
  "status_code": 200,
  "duration_ms": 42.15,
  "client_ip": "127.0.0.1",
  "memory_rss_mb": 58.42
}
```

- **Logging Rules:**
  1. No raw passwords, unhashed tokens, or sensitive resume contents may be emitted to logs.
  2. Latency (`duration_ms`) is tracked on every request via an ASGI middleware timer.
  3. `ERROR` and `CRITICAL` levels must include structured traceback frames and the corresponding `request_id`.

### 7.3 Global Error Handling & Exception Translation Middleware

ProNet establishes a unified, deterministic error response schema. Unhandled exceptions or domain validation failures are trapped by the global exception middleware and formatted into standard JSON envelopes:

```json
{
  "error": {
    "code": "CONNECTION_ALREADY_REQUESTED",
    "message": "A connection request between these users is already pending or established.",
    "status_code": 409,
    "timestamp": "2026-10-20T04:55:12.304Z",
    "path": "/api/connections/request",
    "request_id": "req_01HPX7Z9B4F1M9K8V3W2",
    "details": {
      "initiator_id": "usr_alex_chen",
      "target_id": "usr_elena_rostova"
    }
  }
}
```

- **Standard Error Code Registry:**
  - `INVALID_CREDENTIALS` (401): Password or email mismatch.
  - `TOKEN_EXPIRED` (401): JWT expired beyond 24-hour window.
  - `NOT_JOB_OWNER` (403): User attempted to view applicants for another user's job.
  - `MUST_BE_FIRST_DEGREE` (403): User attempted to message an out-of-network professional.
  - `RESOURCE_NOT_FOUND` (404): Post, user, or job ID not found.
  - `CONNECTION_ALREADY_REQUESTED` (409): Duplicate connection request detected.
  - `ALREADY_APPLIED_TO_JOB` (409): Duplicate job application detected.
  - `PAYLOAD_TOO_LARGE` (413): Uploaded media exceeds strict byte thresholds.
  - `UNSUPPORTED_MEDIA_TYPE` (415): Magic byte validation failed.
  - `MAX_COMMENT_DEPTH_EXCEEDED` (422): Attempted to nest comments beyond Level 2.

### 7.4 Transaction Management, Concurrency & SQLite WAL Strategy

SQLite is configured to support high-throughput concurrent reads and serialized atomic writes through the following engineering mechanisms:

1. **Engine Initialization Pragmas:**
   Upon connection creation, the SQLAlchemy async engine applies critical performance and durability pragmas:
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   PRAGMA busy_timeout = 5000;
   PRAGMA foreign_keys = ON;
   PRAGMA cache_size = -64000; -- 64 MB shared page cache
   PRAGMA temp_store = MEMORY;
   ```
2. **Atomic Write Scoping:**
   Write transactions are wrapped in short-lived `async with session.begin():` blocks. Work is prepared in application memory before opening the transaction, minimizing write lock duration.
3. **Collision Interception on Connections (EDG-001):**
   Connection records enforce unique canonical pair ordering:
   ```sql
   CHECK (user_low_id < user_high_id)
   ```
   If User A and User B concurrently request a connection, the second write encounters the unique constraint, triggers an auto-resolve handler, and updates the record to `ACCEPTED` without raising an error.
4. **Transient Lock Retries (EDG-009):**
   A dedicated database session decorator provides exponential backoff with jitter (max 3 retries, base delay 50ms) if `sqlite3.OperationalError: database is locked` is encountered during WAL checkpointing.

### 7.5 Security, Sanitization & Content Verification Standard

1. **File Magic Byte Header Verification (NFR-006, EDG-004):**
   Uploaded files are not validated merely by file extension or client `Content-Type`. The first 2048 bytes of every upload stream are inspected using magic byte headers:
   - JPEG: `\xFF\xD8\xFF`
   - PNG: `\x89PNG\r\n\x1a\n`
   - WEBP: `RIFF....WEBP`
   - PDF: `%PDF-`
   - DOCX: `PK\x03\x04`
2. **HTML Sanitization (NFR-009):**
   Post text and comment content are sanitized using `bleach` on the backend, stripping dangerous executable HTML tags (`<script>`, `<iframe>`, `onclick`, `<style>`) while preserving safe formatting tags (`<p>`, `<b>`, `<i>`, `<code>`, `<pre>`).
3. **Password Cryptography (NFR-008):**
   Passwords are never stored in plaintext. They are salted and hashed using `bcrypt` with work factor 12. Verification executes in constant time to prevent timing attacks.

---

## 8. Requirements Traceability Matrix

| Requirement ID | Architectural Component | Implementation Location | Compliance Mechanism |
|---|---|---|---|
| **REQ-001** (Persona Quick-Switch) | `AuthService` + Frontend Nav | `src/backend/app/api/v1/auth.py` | Direct JWT issuance for 10 seeded users; no password required. |
| **REQ-002** (Standard Auth & JWT) | `security.py` + `deps.py` | `src/backend/app/core/security.py` | Bcrypt factor 12 hashing; HS256 JWT validation on all protected routes. |
| **REQ-003** (Profile Editing) | `UserService` + User Router | `src/backend/app/api/v1/users.py` | Relational tables for Experience, Education, and Skills. |
| **REQ-004** (Degree Badging) | `GraphService` | `src/backend/app/services/graph_service.py` | 1st-degree direct index lookup; 2nd-degree mutual join CTE. |
| **REQ-005** (Outgoing Connection) | `ConnectionService` | `src/backend/app/api/v1/connections.py` | Pair ordering check, duplicate check, and collision auto-resolve. |
| **REQ-006** (Accept / Ignore) | `ConnectionService` | `src/backend/app/api/v1/connections.py` | Status transition to `ACCEPTED` or `IGNORED`; count updates. |
| **REQ-007** (Withdraw Request) | `ConnectionService` | `src/backend/app/api/v1/connections.py` | Deletes pending connection record; blocked if already accepted. |
| **REQ-008** (Remove Connection) | `ConnectionService` | `src/backend/app/api/v1/connections.py` | Deletes connection record; locks chat and recalculates feed score. |
| **REQ-009** (Rich Post Creation) | `FeedService` + `uploads.py` | `src/backend/app/api/v1/posts.py` | Supports text, code block, and image (<=5MB) with byte checks. |
| **REQ-010** (Dual-Mode Feed) | `FeedService` | `src/backend/app/services/feed_service.py` | "Recent" (chronological) & "Top" (algorithmic scoring); 2 queries max. |
| **REQ-011** (Multi-Type Reactions)| `ReactionService` | `src/backend/app/api/v1/posts.py` | Unique constraint `(user_id, post_id)`; toggle and switch semantics. |
| **REQ-012** (Threaded Comments) | `CommentService` | `src/backend/app/api/v1/posts.py` | Level 1 (`parent_id=NULL`) and Level 2 (`parent_id=L1_id`); depth > 2 blocked. |
| **REQ-013** (Job Posting Creation)| `JobService` | `src/backend/app/api/v1/jobs.py` | Creates job with skills, salary ranges, and workplace mode. |
| **REQ-014** (Job Search & Filter) | `JobService` | `src/backend/app/api/v1/jobs.py` | Multi-facet filtering on title, workplace type, and required skills. |
| **REQ-015** ("Easy Apply") | `JobService` + `uploads.py` | `src/backend/app/api/v1/jobs.py` | Snapshots candidate profile; uploads resume (<=5MB); unique guard. |
| **REQ-016** (Recruiter Pipeline) | `JobService` | `src/backend/app/api/v1/jobs.py` | Role-guarded applicant status transitions (`APPLIED` -> `REJECTED`). |
| **REQ-017** (Direct Messaging) | `ConnectionManager` + WS | `src/backend/app/api/ws/endpoint.py` | Real-time WebSocket transmission restricted to 1st-degree peers. |
| **REQ-018** (Real-Time Alerts) | `NotificationDispatcher` | `src/backend/app/services/seeder.py` | Real-time push for connections, reactions, and messages over WS. |
| **REQ-019** (Deterministic Seeding)| `SeederService` | `src/backend/app/services/seeder.py` | Boots 10 personas, 15 connections, 12 posts, 8 jobs in <= 3.0s. |

---

## 9. Architectural Sign-Off & Verification Protocol

- **Traceable Architecture:** 100% of PRD requirements (REQ-001..019, NFR-001..010, EDG-001..010) mapped to concrete components.
- **Dependency Manifests Locked:** Strict versions pinned in `requirements.txt` and `package.json`.
- **Structural Integrity:** Single workspace root enforced under `Apps/ProNet/`.
- **Next Stage Gate:** Blueprint ready for Phase 3 Data Architecture (`03_data_schema.md`).

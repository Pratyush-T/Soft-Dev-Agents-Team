# ProNet — Professional Network & Career Platform

A full-featured, enterprise-grade professional networking platform (LinkedIn-class) engineered for **100% local operation with zero cloud dependencies**.

Built with **React 18 + TypeScript + Tailwind CSS** on the frontend, **Python FastAPI + SQLAlchemy 2.0 Async** on the backend, and an optimized **SQLite Write-Ahead Logging (`WAL`)** database engine with full-duplex **WebSockets** for real-time messaging and unread notification badges.

---

## Architecture Topology

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND CLIENT                        │
│   React 18  •  TypeScript 5.3  •  Vite 5  •  Tailwind CSS   │
│         Zustand Global Stores  •  Lucide Icons              │
└──────────────────────────────▲──────────────────────────────┘
                               │ HTTP REST & WebSockets (/ws)
┌──────────────────────────────▼──────────────────────────────┐
│                      BACKEND SERVER                         │
│        Python 3.12+  •  FastAPI (ASGI)  •  Uvicorn          │
│       Pydantic v2 Validation  •  PyJWT & Passlib Bcrypt     │
└──────────────────────────────▲──────────────────────────────┘
                               │ Async ORM (aiosqlite)
┌──────────────────────────────▼──────────────────────────────┐
│                    DATABASE & STORAGE                       │
│    SQLite 3.40+ (WAL Mode)  •  SQLAlchemy 2.0 Async Core    │
│           Local Static Storage (/uploads)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3-Step Quickstart

### Option A: 1-Click Launch (Windows)
Double-click [`start.bat`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/start.bat) or run from terminal:
```cmd
cd Apps\ProNet
start.bat
```

### Option B: Manual Launch

1. **Start Backend Server:**
   ```powershell
   cd Apps/ProNet/src/backend
   pip install -r requirements.txt
   python seed_data.py
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *FastAPI Swagger documentation live at:* [**http://localhost:8000/docs**](http://localhost:8000/docs)

2. **Start Frontend Web SPA:**
   ```powershell
   cd Apps/ProNet/src/frontend
   npm run dev
   ```
   *Web application live at:* [**http://localhost:5173**](http://localhost:5173)

---

## 1-Click Persona Quick-Switcher

During local evaluation, use the **Persona Switcher** dropdown in the top-right navbar to instantly switch accounts between 10 realistic seeded professionals with zero password re-entry:

1. **Elena Rostova** — Staff AI Systems Engineer (Active Primary Persona)
2. **Alex Chen** — Senior Full-Stack Engineer (1st Degree Connection)
3. **Marcus Vance** — Engineering Director (1st Degree Connection)
4. **Priya Sharma** — Principal Product Manager (1st Degree Connection)
5. **Devon Taylor** — VP of Engineering (1st Degree Connection)
6. **Sarah Jenkins** — Tech Talent Acquisition Lead / Recruiter (2nd Degree Mutual)
7. **Liam Patel** — DevOps & Cloud Platform Architect (2nd Degree Mutual)
8. **Zack Kowalski** — Security Engineer (3rd Degree Out-of-Network)
9. **Aisha Diop** — Lead UI/UX Designer (2nd Degree Mutual)
10. **Jordan Mendez** — Data Platform Engineer (2nd Degree Mutual)

---

## Core Features & Workflow Guide

1. **Rich Identity & Degree Graph:**
   - Work experience timeline, education, and tag-based skills.
   - Dynamic degree badges: **1st Degree** (connected), **2nd Degree** (mutual connections), and **3rd+ Degree**.
2. **Activity Feed & Reactions:**
   - Post text, code snippets (with language tags), and image attachments.
   - Dual-mode sorting: **Recent** (reverse-chronological) and **Top** (algorithmic engagement score).
   - Multi-reactions: **Like**, **Celebrate**, and **Insightful**.
   - 2-level threaded comments with author moderation.
3. **Job Board & Mini-ATS Pipeline:**
   - Multi-facet search (Remote / Hybrid / On-Site, location, skill tags).
   - "Easy Apply" with candidate profile snapshot and resume upload.
   - Recruiter ATS status pipeline (`Applied` → `Reviewing` → `Shortlisted` → `Rejected`).
4. **Real-Time Direct Messaging:**
   - Private 1-on-1 messaging strictly for confirmed 1st-degree connections.
   - Collapsible Chat Dock with live unread badge counters.

---

## Running the Automated Test Suite

```powershell
python -m pytest Apps/ProNet/tests/test_pronet_suite.py -v
```
*Current test suite status:* **9 passed in 1.74s (100% Green)**.

---

## Documentation Artifacts (Fortune 500 / Big 4 Standards)

| Deliverable | Markdown Specification | Microsoft Word Document (.docx) |
|---|---|---|
| **Product Spec (PRD)** | [`docs/01_prd.md`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/01_prd.md) | [`docs/word/ProNet_Product_Requirements_Document_v1.0.docx`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/word/ProNet_Product_Requirements_Document_v1.0.docx) |
| **System Architecture** | [`docs/02_architecture.md`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/02_architecture.md) | [`docs/word/ProNet_System_Architecture_v1.0.docx`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/word/ProNet_System_Architecture_v1.0.docx) |
| **Data Architecture** | [`docs/03_data_schema.md`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/03_data_schema.md) | [`docs/word/ProNet_Data_Schema_v1.0.docx`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/word/ProNet_Data_Schema_v1.0.docx) |
| **API Contracts** | [`docs/04_api_contracts.md`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/04_api_contracts.md) | N/A |
| **UI/UX Design System** | [`docs/05_ui_system.md`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/05_ui_system.md) | N/A |
| **QA Test Report** | [`docs/08_test_report.md`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/08_test_report.md) | [`docs/word/ProNet_Test_Report_v1.0.docx`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/word/ProNet_Test_Report_v1.0.docx) |
| **Security & Code Audit** | [`docs/09_audit_report.md`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/09_audit_report.md) | [`docs/word/ProNet_Audit_Report_v1.0.docx`](file:///c:/Users/praty/Downloads/Soft%20Dev%20Agents%20Team/Apps/ProNet/docs/word/ProNet_Audit_Report_v1.0.docx) |

# Employee Onboarding Workflow Automator

Enterprise onboarding operations platform with workflow orchestration, task tracking, notifications, analytics, and a retrieval-grounded AI assistant.

This README reflects the code currently implemented in this repository.

## Documentation Index

Core project documents:
1. [Requirements](REQUIREMENTS.md)
2. [Specification](SPEC.md)
3. [Project Plan](PLAN.md)
4. [Deliverables](DELIVERABLES.md)

Documentation hub:
1. [docs/README.md](docs/README.md)

Architecture documents:
1. [Architecture Overview](docs/architecture/ARCHITECTURE.md)
2. [System Design](docs/architecture/SYSTEM_DESIGN.md)
3. [Frontend Architecture](docs/architecture/FRONTEND_ARCHITECTURE.md)
4. [Backend Architecture](docs/architecture/BACKEND_ARCHITECTURE.md)
5. [AI Orchestration](docs/architecture/AI_ORCHESTRATION.md)
6. [RAG Architecture](docs/architecture/RAG_ARCHITECTURE.md)
7. [Database Schema](docs/architecture/DB_SCHEMA.md)
8. [API Contracts](docs/architecture/API_CONTRACTS.md)
9. [Security](docs/architecture/SECURITY.md)
10. [Workflow States](docs/architecture/WORKFLOW_STATES.md)
11. [Primary Architecture Diagram](docs/architecture/architecture.mmd)

Planning documents:
1. [Planning Folder](docs/planning)

Deployment documents:
1. [Deployment Guide](docs/deployment/DEPLOYMENT.md)
2. [Setup Guide](docs/deployment/SETUP_GUIDE.md)
3. [Docker References](docs/deployment/DOCKER_REFERENCES.md)

Validation and review documents:
1. [Reviews Folder](docs/reviews)

Walkthrough documents:
1. [Walkthrough Folder](docs/walkthrough)

Archived development documents:
1. [Archive Folder](docs/archive)

## Project Overview

The application supports the full onboarding operational loop:
1. HR/admin users authenticate.
2. Employee onboarding records are created.
3. Workflows and tasks are tracked through onboarding states.
4. Orchestration events and notifications are generated.
5. Dashboard analytics expose operational status.
6. AI assistant answers onboarding questions using uploaded policy documents.

## Features

### Backend
1. FastAPI async API with layered services.
2. JWT cookie-based authentication (httpOnly).
3. Employee CRUD APIs with automatic company email provisioning.
4. Workflow and task APIs.
5. LangGraph orchestration service:
   - task blueprint generation,
   - workflow state derivation,
   - escalation event generation,
   - persisted orchestration event log.
6. Notification center APIs (list, unread count, mark read, mark all read).
7. RAG APIs (upload/search/chat/list/delete) with ChromaDB.
8. Analytics aggregate endpoint for dashboard metrics.
9. Analytics report exports (workflow, employee, audit) in CSV/PDF.
10. SMTP email delivery:
    - Company email generation (firstname.lastname@company.local) on employee creation.
    - Welcome email sent to employee, manager, and HR on employee creation.
    - Workflow milestone emails at: Onboarding Started, HR Review Completed, IT Provisioning Completed, Documents Shared, Onboarding Completed.
    - Every workflow email also creates an in-app notification.
11. Google OAuth login (authorization-code and token-based endpoints).
12. Health and DB diagnostics endpoints.

### Frontend
1. React + TypeScript + Tailwind + TanStack Query + Zustand.
2. Protected route app shell and auth bootstrap.
3. Pages:
   - Login
   - Dashboard
   - Create Employee
   - Onboarding List
   - Onboarding Detail
   - Notifications
   - Analytics
   - AI Assistant
   - Profile
4. Error boundary and lazy-loaded page routes.
5. Dashboard/analytics modernization with expanded KPI and timeline widgets.
6. Dark mode with persisted user preference.
7. Analytics export controls for CSV/PDF downloads.
8. Login supports Google SSO entry point.

## Architecture

### Backend layering
API routes -> services -> schemas -> models -> database

### Frontend layering
pages -> components -> hooks -> API client/store

### AI and data
1. LiteLLM proxy for chat and embeddings.
2. LCEL chat chain for RAG responses.
3. LangGraph state machine for onboarding orchestration.
4. PostgreSQL for transactional data.
5. ChromaDB for vector retrieval.
6. Disk storage for uploaded RAG documents.

Architecture diagram: see docs/architecture/architecture.mmd

## Setup Instructions

### Prerequisites
1. Python 3.11+
2. Node.js 18+
3. Docker + Docker Compose (recommended local run)

### Option A: Docker Compose (recommended)

1. Create environment file at repo root (if needed for secrets).
2. Provide LiteLLM and JWT values.
3. Start stack:

```bash
docker-compose up -d
```

4. Run migrations inside backend container:

```bash
docker-compose exec backend alembic upgrade head
```

5. Access:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs

### Option B: Local development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python main.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (core)
1. DATABASE_URL
2. JWT_SECRET_KEY
3. COOKIE_SECURE
4. LITELLM_PROXY_URL
5. LITELLM_API_KEY
6. CHROMADB_HOST
7. CHROMADB_PORT
8. UPLOAD_DIR
9. DB_SSL_REQUIRE
10. DB_CONNECT_TIMEOUT
11. DB_COMMAND_TIMEOUT
12. SMTP_ENABLED
13. SMTP_USE_TLS
14. SMTP_SERVER
15. SMTP_PORT
16. SMTP_USERNAME
17. SMTP_PASSWORD
18. SENDER_EMAIL
19. SMTP_FROM_NAME
20. GOOGLE_CLIENT_ID
21. GOOGLE_CLIENT_SECRET
22. GOOGLE_REDIRECT_URI
23. FRONTEND_URL

### Frontend
1. VITE_API_URL
2. VITE_WS_URL (optional; frontend hook exists, backend WS endpoint currently not implemented)
3. VITE_GOOGLE_CLIENT_ID (optional for UI affordance; backend OAuth redirect flow does not require frontend SDK)

## Deployment

Current repository includes:
1. docker-compose.yml for local multi-service deployment.
2. Dockerfile, Dockerfile.backend, Dockerfile.frontend.

Runtime notes:
1. Backend supports Supabase/Postgres-compatible DATABASE_URL.
2. For Supabase pooler mode, asyncpg compatibility settings are already configured in backend/app/db/session.py.

## Current Status

Implemented and available:
1. Auth, employee, onboarding, notification, rag, analytics APIs.
2. Frontend pages for all MVP flows listed above.
3. LangGraph orchestration with event persistence.
4. Chroma-backed RAG with per-user collections.

Known implementation gaps (tracked as future scope):
1. No backend websocket notification endpoint (UI currently relies on polling; websocket hook is optional).
2. Calendar provider integrations (Google/Microsoft) are not implemented; current scheduling is internal MVP calendar.
3. Email/SMS provider integrations beyond SMTP transport are not implemented.

## API Summary

Base path: /api/v1

Resource groups:
1. /auth
2. /employees
3. /onboarding
4. /notifications
5. /rag
6. /analytics

Health endpoints:
1. /health
2. /health/db

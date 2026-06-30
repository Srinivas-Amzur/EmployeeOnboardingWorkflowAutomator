# 1. Project Overview

## Application Summary
Employee Onboarding Workflow Automator is an enterprise onboarding operations platform that centralizes employee onboarding workflows, task tracking, meeting scheduling, notifications, analytics, and retrieval-grounded AI assistance.

## Business Problem Solved
HR, IT, and managers need one operational system to:
- orchestrate onboarding from initiation to completion,
- avoid manual handoff gaps across departments,
- track state and SLAs with visibility,
- notify stakeholders on actionable events,
- answer onboarding policy questions from internal documents.

## Architecture Style
The implemented architecture is layered and service-centric:
- Backend: router -> service -> schema -> model.
- Frontend: pages -> components -> hooks -> API client or store.
- AI runtime: deterministic LangGraph orchestration plus RAG chat pipeline.

Primary implementation evidence:
- backend/app/api/v1 and backend/app/services
- frontend/src/pages, frontend/src/components, frontend/src/hooks, frontend/src/lib/api.ts
- .github/copilot-instructions.md

---

# 2. Frontend Stack

| Technology | Version (declared) | Purpose | Where used |
|---|---:|---|---|
| React | 18.2.0 | Component UI runtime | frontend/src/App.tsx, frontend/src/pages |
| TypeScript | 5.3.3 | Static typing and build-time safety | frontend/tsconfig.json, frontend/src |
| Vite | 5.0.8 | Dev server and production bundling | frontend/package.json scripts, frontend/vite.config.ts |
| React Router DOM | 6.21.0 | Client-side routing and protected navigation | frontend/src/App.tsx, frontend/src/components/common/ProtectedRoute.tsx |
| TanStack React Query | 5.28.0 | Server-state fetching, caching, mutation handling | frontend/src/App.tsx, frontend/src/hooks/index.ts |
| Zustand | 4.4.5 | Lightweight client-side state stores | frontend/src/store/index.ts |
| Axios | 1.6.2 | HTTP client for API integration | frontend/src/lib/api.ts |
| Tailwind CSS | 3.4.1 | Utility-first styling system | frontend/tailwind.config.js, frontend/src/**/*.tsx |
| PostCSS + Autoprefixer | 8.4.32, 10.4.16 | CSS processing pipeline | frontend/postcss.config.js |
| Recharts | 3.8.1 | Dashboard and analytics chart rendering | frontend/src/pages/DashboardPage.tsx, frontend/src/pages/AnalyticsDashboard.tsx |
| Headless UI | 1.7.17 | Accessible unstyled UI primitives (dialogs, menus) | frontend/src/components/common/ChangePasswordModal.tsx, frontend/src/components/layout/Navbar.tsx |
| Framer Motion | 11.18.2 | Page/layout animation | frontend/src/components/layout/Layout.tsx |
| Lucide React | 1.17.0 | Icon system across UI screens | frontend/src/pages, frontend/src/components/layout |
| React Error Boundary | 6.1.2 | Global runtime error fallback boundary | frontend/src/App.tsx |
| React Markdown + remark-gfm | 10.1.0, 4.0.1 | Rich markdown rendering in AI assistant answers | frontend/src/pages/AIAssistantPage.tsx |

---

# 3. Backend Stack

## Core Runtime

| Category | Technology | Version (declared) | Evidence |
|---|---|---:|---|
| Programming language | Python | 3.11 (image and docs baseline) | Dockerfile.backend, backend/requirements.txt |
| Web/API framework | FastAPI | 0.109.0 | backend/app/main.py, backend/app/api/v1 |
| ASGI server | Uvicorn | 0.27.0 | backend/main.py, Dockerfile.backend |
| ORM | SQLAlchemy async 2.0 style | 2.0.25 | backend/app/models, backend/app/db/session.py |
| Validation and settings | Pydantic + pydantic-settings | 2.5.2, 2.1.0 | backend/app/schemas, backend/app/core/config.py |
| DB drivers | asyncpg primary, psycopg2 for Alembic sync path | 0.29.0, 2.9.9 | backend/app/db/session.py, backend/app/db/migrations/env.py |
| API dependency system | FastAPI Depends and typed DI aliases | n/a | backend/app/api/dependencies.py, endpoint modules |

## Backend Design Characteristics
- Async request handling with async DB sessions.
- Strict separation of API layer and business logic services.
- Pydantic request and response contracts in backend/app/schemas.
- JWT cookie auth and role-based authorization checks at dependency and route levels.

---

# 4. Database Technologies

| Technology | Status in repository | Purpose | Where verified |
|---|---|---|---|
| PostgreSQL | Implemented primary transactional store | Users, employees, workflows, tasks, meetings, notifications, orchestration events | docker-compose.yml (postgres service), backend/app/models, backend/app/db/session.py |
| Supabase (Postgres-compatible) | Implemented compatibility path | Managed Postgres deployment target with connection hardening | backend/app/core/config.py using_supabase(), backend/app/db/session.py NullPool and asyncpg compatibility settings |
| ChromaDB | Implemented vector store | Per-user vector collections for RAG retrieval | docker-compose.yml (chromadb service), backend/app/services/vector_store.py |
| Alembic | Implemented migration framework | Schema migration versioning and execution | backend/app/db/migrations/alembic.ini, backend/app/db/migrations/versions |

Migration versions present: 6 files in backend/app/db/migrations/versions.

---

# 5. AI and LLM Stack

## Technologies in Use

| Technology | Version (declared) | Role in system | Evidence |
|---|---:|---|---|
| LangGraph | 0.0.18 | Deterministic onboarding state-machine orchestration | backend/app/ai/orchestrator.py, backend/app/services/orchestration.py |
| LangChain | 0.1.7 | RAG workflow primitives and text-splitting compatibility | backend/app/services/document_processing.py, backend/app/services/ai_chat.py |
| langchain-openai | 0.0.5 | ChatOpenAI and OpenAIEmbeddings clients via LiteLLM proxy | backend/app/ai/llm.py |
| LiteLLM proxy integration | via base_url and API key config | Model routing and unified provider gateway | backend/app/ai/llm.py, backend/app/core/config.py |
| ChromaDB | 0.4.20 | Embedding storage and semantic retrieval | backend/app/services/vector_store.py |
| OpenAI embeddings endpoint | text-embedding-3-large | Embedding generation for chunk and query vectors | backend/app/ai/llm.py |
| Chat models | gemini/gemini-2.5-flash and gpt-4o | Fast path and advanced reasoning path | backend/app/ai/llm.py |
| LCEL prompt orchestration | prompt | llm | parser composition | backend/app/ai/chains/rag_chain.py |
| RAG pipeline | Implemented end-to-end | Upload PDF, extract text, chunk, embed, store, retrieve, answer with citations | backend/app/services/document_processing.py, vector_store.py, rag.py, ai_chat.py |

## Why these were selected in this implementation
- LangGraph: used for explicit workflow state transitions and deterministic orchestration logic suitable for operational onboarding.
- LangChain and LCEL: enables composable prompt pipelines and chat-history-aware context execution without custom framework plumbing.
- LiteLLM proxy: centralizes model access and model switching while keeping app code stable.
- ChromaDB: lightweight vector retrieval with per-user isolation strategy user_{user_id}.
- OpenAI-compatible embeddings via proxy: consistent embedding interface aligned with the existing LiteLLM setup.

---

# 6. Authentication and Security

| Capability | Implementation | Where verified |
|---|---|---|
| JWT | Token creation and decode using jose JWT APIs | backend/app/core/security.py |
| HTTP-only cookies | Access token stored in cookie with httponly and secure controls | backend/app/api/v1/endpoints/auth.py |
| Google OAuth | Authorization-code flow and ID token flow endpoints | backend/app/api/v1/endpoints/auth.py, backend/app/services/auth.py |
| RBAC | Role checks at route and dependency level for admin or hr_admin and scoped role logic in services | backend/app/api/dependencies.py, endpoint files, audit and analytics services |
| Password hashing | passlib CryptContext with bcrypt | backend/app/core/security.py |
| Authorization strategy | Dependency-injected current user from cookie JWT plus endpoint-level role and ownership constraints | backend/app/api/dependencies.py, onboarding and meetings endpoints |

Additional implemented security-relevant controls:
- Secure cookie toggle via COOKIE_SECURE.
- Upload validation for RAG ingestion (PDF-only path).
- CORS and centralized error and request middleware.

---

# 7. Notifications

| Area | Implementation status | Evidence |
|---|---|---|
| In-app notifications | Implemented with persistent notifications table and REST APIs | backend/app/models/notification.py, backend/app/api/v1/endpoints/notifications.py |
| SMTP email notifications | Implemented as best-effort SMTP transport, provider-level integrations not implemented | backend/app/services/email_service.py, backend/app/services/notification.py |
| Notification architecture | Event-to-notification mapping in service layer; read and unread APIs | backend/app/services/notification.py |

Implemented notification API surface:
- list notifications,
- unread count,
- mark single read,
- mark all read.

---

# 8. Reporting and Analytics

| Capability | Implementation | Evidence |
|---|---|---|
| Dashboard metrics | Aggregated workflow, task, employee and completion metrics endpoint | backend/app/api/v1/endpoints/analytics.py, backend/app/services/analytics.py |
| Charts | Recharts visualizations in dashboard and analytics pages | frontend/src/pages/DashboardPage.tsx, frontend/src/pages/AnalyticsDashboard.tsx |
| CSV export | Analytics export endpoint supports csv format | backend/app/api/v1/endpoints/analytics.py, frontend/src/pages/AnalyticsDashboard.tsx |
| PDF export | Analytics export endpoint supports pdf format via ReportLab | backend/app/api/v1/endpoints/analytics.py |

---

# 9. DevOps and Deployment

| Area | Technology or approach | Evidence |
|---|---|---|
| Containerization | Docker (separate backend, frontend, and full-stack Dockerfiles) | Dockerfile, Dockerfile.backend, Dockerfile.frontend |
| Local orchestration | Docker Compose with postgres, chromadb, backend, frontend services | docker-compose.yml |
| Environment configuration | Environment-variable-driven config via pydantic-settings and .env loading | backend/app/core/config.py |
| Backend runtime | Uvicorn ASGI app serving FastAPI | backend/main.py, Dockerfile.backend |
| Deployment approach in repo | Dockerized local and portable container deployment baseline | docker-compose.yml and deployment docs |

Notes:
- Supabase compatibility exists in runtime DB session code.
- Kubernetes and ECS are discussed in docs as recommendations, not as implemented deployment manifests in this repository.

---

# 10. Development Tools

| Tooling | Status | Where verified |
|---|---|---|
| Git | Repository version control present | .git directory |
| GitHub Copilot | Repository contains Copilot instruction policy file | .github/copilot-instructions.md |
| VS Code workflow | Project contains VS Code workspace settings | .vscode directory |
| Python formatting or linting | black, ruff, mypy declared | backend/requirements.txt |
| Frontend linting | eslint and TypeScript ESLint plugins declared | frontend/package.json |
| Testing tools | pytest, pytest-asyncio, httpx, aiosqlite | backend/requirements.txt, backend/tests |
| Claude Code | No direct repository artifact proving it was used | no explicit config or instructions file naming Claude |

---

# 11. Architecture and Design Patterns

Patterns confirmed in implementation:

| Pattern | Implemented | Evidence |
|---|---|---|
| Layered architecture | Yes | backend/app/api, services, schemas, models |
| Router -> Service -> Model flow | Yes | endpoint modules calling service classes, services using models |
| Dependency injection | Yes | FastAPI Depends and typed aliases in dependencies.py |
| Component-based UI | Yes | frontend/src/components and frontend/src/pages composition |
| State machine orchestration | Yes | LangGraph StateGraph in backend/app/ai/orchestrator.py |
| Specification-driven development | Yes | REQUIREMENTS.md and SPEC.md aligned to implemented scope |
| AI-first workflow augmentation | Yes | Orchestration and RAG integrated as first-class system modules |

Pattern not explicitly implemented as a separate abstraction:
- Repository pattern as a distinct repository class layer is not present; services directly execute SQLAlchemy queries.

---

# 12. Testing Strategy

## Backend tests
- Test framework: pytest with async support.
- Unit tests: backend/tests/unit.
- Integration tests: backend/tests/integration.

## Verification workflows used in repository artifacts
- Backend test execution with pytest.
- Frontend production build verification via npm run build.
- Dependency verification via pip check.

## Scope characteristics
- Auth, RBAC, onboarding workflows, orchestration, notifications, analytics, and RAG service behavior are covered by test files.
- No frontend automated test framework configuration is present in package scripts.

---

# 13. Project Documentation

Major documentation artifacts and purpose:

| File | Purpose |
|---|---|
| README.md | Current implementation overview, setup, envs, feature map |
| REQUIREMENTS.md | Frozen requirement baseline and in or out scope boundaries |
| SPEC.md | Technical specification for models, APIs, states, orchestration, and RAG behavior |
| docs/architecture/ARCHITECTURE.md | High-level architecture narrative |
| docs/architecture/API_CONTRACTS.md | Implementation-verified endpoint contract reference |
| docs/architecture/DB_SCHEMA.md | Implementation-verified data model summary |
| docs/architecture/AI_ORCHESTRATION.md | Orchestration node and AI responsibilities overview |
| docs/deployment/DEPLOYMENT.md | Deployment strategy guidance |
| .github/copilot-instructions.md | Repo-specific engineering and architecture constraints for AI-assisted development |

Additional doc collections:
- docs/planning for planning and product docs,
- docs/reviews for validation and readiness reports,
- docs/walkthrough for demonstration and walkthrough material,
- docs/archive for historical implementation notes.

---

# 14. Repository Statistics

Counts generated from repository scan on 2026-06-27.

| Metric | Count | Counting rule |
|---|---:|---|
| Frontend pages | 11 | frontend/src/pages/*.tsx |
| Backend modules | 71 | backend/app/**/*.py |
| API endpoints | 48 total | 46 route decorators in backend/app/api/v1/endpoints plus 2 health endpoints in backend/app/main.py |
| Database models | 7 | SQLAlchemy model classes inheriting Base in backend/app/models |
| Migrations | 6 | backend/app/db/migrations/versions/*.py |
| Documentation files | 64 markdown files | docs/**/*.md (54) plus root *.md (10) |
| Backend test files | 9 | backend/tests/**/test_*.py |
| Backend test functions | 100 | functions named test_ in backend/tests |

## Total Repository Structure Summary

High-level workspace composition:
- Top-level operational directories: backend, frontend, docs, uploads, plus config directories such as .github and .vscode.
- Frontend source files: 37 files under frontend/src.
- Backend application code: 71 Python modules under backend/app.
- Backend tests: 34 files total under backend/tests, including fixtures and test modules.

---

# 15. Technology Selection Rationale

This stack is a strong fit for an AI-powered enterprise onboarding platform because:

1. FastAPI plus async SQLAlchemy provides high productivity, explicit schemas, and scalable async I or O for API-heavy workflows.
2. PostgreSQL gives reliable transactional guarantees for onboarding state, task lifecycle, and audit-relevant records.
3. LangGraph introduces deterministic orchestration for multi-stage onboarding, which is safer for operational workflows than unconstrained agent loops.
4. LangChain plus LCEL and LiteLLM provides a clean abstraction for prompt pipelines while preserving model portability.
5. ChromaDB enables practical per-user retrieval isolation for policy-grounded assistant responses.
6. React plus TypeScript plus TanStack Query offers fast enterprise UI iteration with strong client-state and server-state separation.
7. Docker and Compose make the stack reproducible for local validation, demos, and capstone walkthroughs.
8. Security choices (JWT cookie auth, RBAC, bcrypt hashing, Google OAuth support) align with enterprise onboarding requirements while remaining implementation-realistic for MVP scope.

In short, the repository uses a pragmatic hybrid architecture: deterministic business orchestration for core onboarding operations, and AI augmentation where retrieval and conversational assistance add measurable productivity.

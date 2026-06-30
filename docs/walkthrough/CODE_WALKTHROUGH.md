# Code Walkthrough - Employee Onboarding Workflow Automator

## Overview
Implemented architecture follows a layered pattern:
- Backend: router -> service -> schema -> model -> database
- Frontend: pages -> components -> hooks -> API client/store

This structure keeps HTTP concerns in routers, business logic in services, and persistence in SQLAlchemy models.

## Frontend Walkthrough

## 1) Folder Structure
`frontend/src` is organized by responsibility:
- `pages/`: route-level screens (Dashboard, Workflows, Notifications, Analytics, AI Assistant, etc.)
- `components/`: reusable UI and layout building blocks
- `hooks/`: TanStack Query hooks and mutation/query orchestration
- `lib/api.ts`: centralized API client and endpoint wrappers
- `store/`: Zustand global state (auth, toast, onboarding view state)
- `types/`: TypeScript contracts aligned with backend payloads

## 2) Routing
Routing uses `react-router-dom` in `App.tsx` with:
- lazy-loaded route pages,
- protected routes for authenticated areas,
- shared app shell via `Layout` + `Navbar`.

Routes implemented:
- `/login`
- `/dashboard`
- `/employees/new`
- `/onboarding`
- `/onboarding/:workflowId`
- `/notifications`
- `/analytics`
- `/assistant`
- `/profile`

## 3) State Management
Two complementary patterns are used:
- **TanStack Query** for server state (fetching, caching, invalidation).
- **Zustand** for local app/session UI state:
  - auth user/session flags,
  - toast list,
  - onboarding UI selection state.

## 4) API Integration
`lib/api.ts` uses Axios with:
- base URL from `VITE_API_URL`,
- `withCredentials: true` for cookie auth,
- grouped API modules: auth, employees, onboarding, analytics, rag, notifications.

Most pages use hooks built on this client. One implemented exception:
- `OnboardingDetailPage` uses direct `fetch` calls (still authenticated via `credentials: include`).

## 5) UI Components
Reusable components include:
- auth/session: `AuthBootstrap`, `ProtectedRoute`
- primitives: `Button`, `Card`, `Skeleton`, `ProgressBar`, `StatusBadge`
- feedback: `ToastContainer`, `EmptyState`
- layout: `Navbar`, `Layout`

Pages compose these components for consistent UX and rapid development.

## Backend Walkthrough

## 1) FastAPI Architecture
Application entry (`backend/app/main.py`) sets up:
- lifespan startup/shutdown,
- DB diagnostics and warmup,
- middleware (error handling and request logging),
- CORS,
- API v1 router registration,
- health endpoints (`/health`, `/health/db`).

API v1 endpoints are grouped by domain:
- auth
- employees
- onboarding
- notifications
- rag
- analytics

## 2) Models (SQLAlchemy)
Core domain models:
- `User`
- `Employee`
- `OnboardingWorkflow`
- `OnboardingTask`
- `Notification`
- `OnboardingOrchestrationEvent`

Common model conventions:
- UUID primary keys (`UUIDMixin`)
- `created_at` / `updated_at` timestamps (`TimestampMixin`)
- timezone-aware datetime columns where applicable

## 3) Schemas (Pydantic)
Typed request/response contracts are defined per domain:
- `schemas/user.py`
- `schemas/employee.py`
- `schemas/onboarding.py`
- `schemas/notification.py`
- `schemas/rag.py`

Examples:
- password complexity and confirmation validation
- typed notification enums
- RAG request bounds (`top_k`, prompt length)

## 4) Services (Business Logic)
Service layer encapsulates domain behavior:
- `AuthService`: auth lookup and password changes
- `EmployeeService`: employee CRUD + orchestration trigger
- `OnboardingService`: workflow/task CRUD + progress + summary
- `OrchestrationService`: LangGraph execution, event persistence, state sync
- `NotificationService`: notification creation/query/read lifecycle
- `AnalyticsService`: aggregated dashboard metrics
- `RAGService`: upload/index/search/chat orchestration

## 5) Routers (HTTP Layer)
Routers handle:
- payload binding and response modeling,
- dependency injection (db session, current user, admin guard),
- HTTP status and error translation.

Routers avoid business logic; they delegate to services.

## 6) Middleware
Implemented middleware includes:
- `ErrorHandlingMiddleware`: structured error responses with request id
- `RequestLoggingMiddleware`: request/response logging with request id context

## 7) Authentication
Auth flow is JWT-in-cookie:
- login issues JWT with claims (`sub`, `email`, `role`, `exp`)
- cookie is `httpOnly` and env-controlled secure flag
- dependencies read/validate cookie token
- role checks enforce admin-only operations for create/update management actions

## AI Layer Walkthrough

## 1) LangGraph Orchestration
`ai/orchestrator.py` defines a deterministic state graph for onboarding lifecycle:
- initialize
- generate HR review tasks
- generate provisioning tasks
- schedule meetings tasks
- share documents tasks
- complete/derive workflow state

It also computes:
- completion percentage,
- state transitions,
- escalation events for overdue tasks.

## 2) Workflow Engine Integration
`OrchestrationService` bridges LangGraph and persistence:
- creates/ensures workflow,
- applies generated task blueprints with deduplication,
- updates workflow/employee statuses,
- persists orchestration events,
- triggers notifications for transitions and escalations,
- re-syncs state whenever tasks change.

## 3) RAG Implementation
RAG stack consists of:
- `DocumentProcessingService`: validate PDF, extract text, chunk content
- `VectorStoreService`: embed/store/query chunks in Chroma
- `AIChatService`: LCEL chain with chat history
- `RAGService`: orchestrates upload/search/chat/list/delete operations

## 4) Document Ingestion
Ingestion path:
1. Receive PDF upload.
2. Validate extension, MIME type, size.
3. Save to uploads directory under user namespace.
4. Extract text from PDF.
5. Split text into overlapping chunks.
6. Generate embeddings.
7. Persist vectors + metadata.
8. Emit indexing-complete notification.

## 5) Vector Search
Search path:
1. Embed query.
2. Query user-specific Chroma collection.
3. Normalize result scores.
4. Build source references and context blocks.
5. Invoke chat chain for grounded answer.

## Database Walkthrough

## 1) SQLAlchemy Models
SQLAlchemy 2.0 async stack is used for all transactional entities. Models map directly to onboarding/auth/notification/orchestration domains.

## 2) Alembic Migrations
Migration chain includes:
- base tables,
- datetime type correction migration,
- orchestration events table,
- notifications table.

Alembic environment resolves DB URL from env/backend `.env` and converts asyncpg URL to psycopg2 for migration execution.

## 3) PostgreSQL / Supabase Integration
DB session layer includes:
- async engine/session factory,
- connectivity diagnostics and startup warmup,
- Supabase-aware configuration (SSL + pooler compatibility),
- health payload for operational checks.

## Request Flow Examples (UI -> API -> Service -> DB)

## A) Create Employee
1. UI (`CreateEmployeePage`) -> `useCreateEmployee` -> `POST /employees`
2. Router (`employees.py`) -> `EmployeeService.create_employee`
3. Service writes `employees` row
4. Service triggers `OrchestrationService.orchestrate_for_employee`
5. Orchestration writes workflow/tasks/events/notifications
6. DB tables touched: `employees`, `onboarding_workflows`, `onboarding_tasks`, `onboarding_orchestration_events`, `notifications`

## B) Update Task Status
1. UI (`OnboardingDetailPage`) -> `PATCH /onboarding/tasks/{id}`
2. Router (`onboarding.py`) -> `OnboardingService.update_task`
3. Service updates task row
4. Service triggers workflow sync via `OrchestrationService.sync_workflow_state`
5. Sync recalculates state, writes events and notifications
6. DB tables touched: `onboarding_tasks`, `onboarding_workflows`, `onboarding_orchestration_events`, `notifications`

## C) Ask AI Assistant
1. UI (`AIAssistantPage`) -> `POST /rag/chat`
2. Router (`rag.py`) -> `RAGService.answer_question`
3. Service performs semantic search in Chroma for user namespace
4. Service builds contextual prompt and invokes LCEL chain
5. Response returns answer + citation metadata
6. Persistent stores touched: Chroma collection and (during upload flow) local uploads path

## Verified Gaps / Incomplete Areas
- frontend has optional WebSocket notification hook, but backend currently has no WebSocket notifications endpoint,
- frontend `getWorkflowSnapshot` path uses `/snapshot` while backend route is `/orchestration`,
- email sender is a placeholder (prints, no provider integration).

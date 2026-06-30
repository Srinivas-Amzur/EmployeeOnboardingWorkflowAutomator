# REQUIREMENTS (Frozen)

Date frozen: 2026-06-01
Source of truth: implemented code in backend/, frontend/, migrations, docker-compose.yml, and current docs.

## Problem Statement
HR and IT teams need a single system to coordinate employee onboarding from intake through completion, with clear workflow state tracking, task orchestration, notifications, analytics, and policy-grounded AI assistance.

## In-Scope Features (Implemented)
1. Authentication and session management
- Register, login, logout, current-user profile, change password
- JWT auth in httpOnly cookie
- Role guard for admin/hr_admin endpoints

2. Employee management
- Create, read, list, update employee records
- Employee onboarding status tracking
- Automatic company email generation (firstname.lastname@company.local) on create
- Company email stored in employee record and returned in all API responses

3. Onboarding workflows and tasks
- Create/list/get/update workflows
- Task create/list/update per workflow
- Workflow progress metrics endpoint
- Employee onboarding summary endpoint

4. LangGraph orchestration
- Deterministic state graph for onboarding stages
- Automatic task blueprint generation by stage
- Workflow state derivation from task completion
- Escalation event generation for overdue tasks
- Orchestration event persistence and retrieval

5. Notifications (in-app)
- Persisted notifications table and API
- List notifications with unread filter/pagination
- Mark one/all as read
- Notifications triggered by task/workflow/AI indexing events

6. SMTP Email delivery
- Welcome email on employee creation: sent to employee, manager, and HR
  - Contains: Employee Name, Employee ID, Company Email, Department, Designation, Start Date, Workflow Status
- Workflow milestone emails sent to employee, manager, and HR when workflow reaches:
  - Onboarding Started (initiated state)
  - HR Review Completed (provisioning state entered)
  - IT Provisioning Completed (meetings_scheduled state entered)
  - Documents Shared (documents_shared state)
  - Onboarding Completed (completed state)
- Each milestone email also creates an in-app notification
- SMTP transport configured via environment variables (no external provider required)

7. RAG assistant
- PDF upload and chunking
- Per-user Chroma collections (user_{user_id})
- Semantic search endpoint
- Grounded chat endpoint with source references
- Document list and delete endpoints

7. Analytics dashboard backend
- Aggregated workflow/task/employee metrics endpoint

8. Frontend MVP screens
- Login, Dashboard, Create Employee, Onboarding list/detail, Notifications, Analytics, AI Assistant, Profile
- Protected routes, global error boundary, lazy-loaded pages

9. Deployment baseline
- Docker Compose services for postgres, chromadb, backend, frontend
- Backend supports Supabase Postgres via DATABASE_URL and asyncpg hardening

## Out-of-Scope Features (Not Implemented)
1. External email provider integrations (Microsoft 365, Google Workspace, SendGrid)
2. Calendar provider integrations (Google/Microsoft)
3. SSO/SAML/OIDC and MFA
4. Native mobile app
5. Multi-tenant org management and white-label branding
6. Full audit logging module for all admin actions
7. Real-time backend websocket notifications endpoint
8. Non-PDF ingestion in RAG pipeline (DOCX/images are not enabled in RAG upload path)
9. Email diagnostics pages, SMTP health dashboard, email retry queues, email template management UI, bulk email features, email analytics

## Assumptions
1. PostgreSQL is reachable through one DATABASE_URL (local Postgres or Supabase/Postgres-compatible endpoint).
2. ChromaDB is reachable by HTTP or local persistent fallback path.
3. LiteLLM proxy URL and API key are provided.
4. Users are created with roles including admin/hr_admin/employee.
5. Onboarding task state values are managed as strings used by services and UI.
6. Frontend and backend are deployed with matching API base URL and cookie policy settings.

## Success Criteria
1. Auth flow works end-to-end: register/login/me/logout/change-password.
2. Admin can create employees and workflows; workflows/tasks are queryable and updateable.
3. Employee creation triggers orchestration and task blueprint creation.
4. Workflow progress and event history are visible through API.
5. Notifications are generated for assignment/completion/orchestration/indexing events.
6. RAG upload->index->search->chat loop works with source citations.
7. Analytics endpoint returns aggregate counts for dashboard views.
8. Frontend navigation supports all MVP pages behind protected auth.

## 2-Week Capacity Reality Check
Realistically deliverable in two weeks for a small team:
1. Core auth + employee CRUD + workflow/task CRUD
2. Deterministic orchestration and event logging
3. In-app notification center API and basic UI
4. Basic RAG with PDF-only ingestion and retrieval-grounded chat
5. One analytics aggregation endpoint and dashboard visualizations
6. Dockerized local run path

Likely post-2-week or deferred items:
1. Enterprise SSO/MFA
2. Email/calendar integrations
3. Full observability/audit framework
4. Strong real-time socket infrastructure
5. E2E test suite and advanced hardening

## Freeze Requirements Statement
This REQUIREMENTS.md is frozen as of 2026-06-01 and must be treated as immutable baseline requirements for review and capstone evaluation. Any future scope changes must be documented separately (see FUTURE_VISION.md) and must not alter this frozen requirements baseline.

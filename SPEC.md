# SPEC

## System Architecture
Backend layers:
1. API routers: FastAPI endpoints in backend/app/api/v1/endpoints
2. Services: business logic in backend/app/services
3. Schemas: pydantic contracts in backend/app/schemas
4. Models: SQLAlchemy 2.0 models in backend/app/models
5. Data stores: PostgreSQL + ChromaDB + disk uploads

Frontend layers:
1. Pages: route-level views
2. Components: reusable UI
3. Hooks: TanStack Query wrappers
4. API client: frontend/src/lib/api.ts
5. Store: Zustand auth/toast/onboarding state

## Data Models
Relational entities (implemented):
1. users
- id, name, email, hashed_password, google_id, role, is_active, created_at, updated_at

2. employees
- id, first_name, last_name, email, department, designation, manager_id, joining_date, onboarding_status, created_at, updated_at

3. onboarding_workflows
- id, employee_id, current_state, completion_percentage, started_at, completed_at, created_at, updated_at

4. onboarding_tasks
- id, workflow_id, title, description, assigned_to, status, priority, due_date, completed_at, created_at, updated_at

5. onboarding_orchestration_events
- id, workflow_id, employee_id, event_type, status, state_from, state_to, message, payload, created_at, updated_at

6. notifications
- id, user_id, notification_type, title, message, is_read, read_at, payload, created_at, updated_at

Vector model:
1. Chroma collection per user: user_{user_id}
2. Chunk metadata: document_id, document_name, document_type, file_path, chunk_index, ingested_at

## API Contracts
Auth:
1. login returns access_token + user; sets access_token cookie
2. me returns authenticated user profile
3. change-password validates current password and rotates cookie token

Employees:
1. admin/hr_admin required for create/list/update
2. authenticated user can get employee detail

Onboarding:
1. workflow CRUD + progress
2. orchestration snapshot/events endpoints
3. workflow task create/list and task patch
4. employee onboarding summary endpoint

Notifications:
1. list endpoint returns items + unread_count
2. unread count endpoint for badge polling
3. mark-read and mark-all-read mutation endpoints

RAG:
1. upload accepts multipart file + document_type
2. chat accepts question/top_k/session_id and returns answer + citations
3. search returns semantic chunk results
4. document list/delete management endpoints

Analytics:
1. dashboard aggregate endpoint returns workflow/task/employee counts and averages

## Workflow State Machine
State set:
1. initiated
2. hr_review
3. provisioning
4. meetings_scheduled
5. documents_shared
6. completed

Transition behavior:
1. New workflow initializes in initiated.
2. Task blueprints generated for hr_review, provisioning, meetings_scheduled, documents_shared.
3. Current state derived from first incomplete stage.
4. Completed when all stage tasks are complete.
5. Escalation events produced for overdue tasks.

## LangGraph Specification
Graph implementation:
1. initialize_workflow
2. generate_tasks (hr_review)
3. provisioning_tasks
4. schedule_meetings
5. share_documents
6. complete_workflow

Graph outputs used by service layer:
1. task_blueprints
2. events
3. notifications
4. escalations
5. current_state
6. completion_percentage

Persistence and side effects:
1. Task blueprints persisted as onboarding_tasks (deduplicated)
2. Events/escalations persisted to onboarding_orchestration_events
3. Notification records created from mapped event types
4. Employee onboarding_status updated to in_progress/completed

## RAG Specification
Ingestion:
1. Only PDF accepted in current ingestion path.
2. MIME type and size validated.
3. File persisted under uploads/rag/user_{user_id}/.
4. PDF text extracted and chunked (1200 size, 220 overlap).
5. Embeddings generated via LiteLLM-configured OpenAIEmbeddings.
6. Chunks stored in Chroma user collection.

Retrieval and QA:
1. Semantic search computes score from distance.
2. Chat builds context from retrieved chunks.
3. LCEL chain (prompt | llm | parser) generates response.
4. Response returns structured source references.

## Notification Specification
Creation triggers:
1. Task assignment
2. Task completion
3. Workflow/orchestration events
4. AI indexing completion

Storage and read model:
1. notifications table with payload JSON
2. unread count by user
3. list ordered newest-first
4. mark one/all as read with timestamp

Delivery mode:
1. API polling is implemented and reliable.
2. Frontend has optional websocket listener hook, but backend websocket endpoint is not implemented in current codebase.

## Authentication Specification
1. Passwords hashed with bcrypt/passlib.
2. JWT signed with HS256 secret.
3. Token includes sub/email/role/exp/iat.
4. Cookie name: access_token; httpOnly; secure controlled by env (COOKIE_SECURE).
5. Authorization dependencies enforce authenticated and admin routes.

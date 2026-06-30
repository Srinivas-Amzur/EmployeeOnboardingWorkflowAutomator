# CHECKPOINTS

## Phase 1 Complete: Core Platform Skeleton
Acceptance criteria:
1. FastAPI app boots with health endpoints.
2. DB session/migrations configured and base tables created.
3. React app routes render with protected route shell.
4. Auth store/bootstrap path exists.

## Phase 2 Complete: Business Core
Acceptance criteria:
1. Auth endpoints operational (register/login/logout/me/change-password).
2. Employee CRUD endpoints operational.
3. Workflow/task CRUD endpoints operational.
4. Frontend pages for login, create employee, workflow list/detail functional.

## Phase 3 Complete: AI + Orchestration + Notifications
Acceptance criteria:
1. LangGraph orchestrator integrated via service layer.
2. Automatic task generation and workflow state sync implemented.
3. Orchestration events persisted and retrievable.
4. Notification model/service/endpoints implemented and UI wired.
5. RAG upload/search/chat/list/delete endpoints operational.

## Phase 4 Complete: Analytics + Delivery Readiness
Acceptance criteria:
1. Analytics dashboard API and frontend views operational.
2. Docker compose stack runs frontend/backend/postgres/chromadb locally.
3. Health/db diagnostics endpoint operational.
4. Validation reports and capstone-ready docs present.

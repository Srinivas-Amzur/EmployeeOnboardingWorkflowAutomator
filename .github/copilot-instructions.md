# AI Forge 2026 - Employee Onboarding Workflow Automator

## Purpose
This repository contains an implemented MVP for enterprise employee onboarding automation.

When generating or modifying code, align with the existing implementation first. Do not assume planned capabilities exist unless they are in code.

## Implemented Architecture

### Backend layering
router -> service -> schema -> model

### Frontend layering
pages -> components -> hooks -> API client/store

### Runtime components
- FastAPI backend
- PostgreSQL (local or managed, typically via DATABASE_URL)
- ChromaDB vector store
- React TypeScript frontend
- LiteLLM proxy for chat and embeddings
- LangGraph for onboarding orchestration

## Implemented Functional Scope
1. Auth (JWT in httpOnly cookies): login, register, logout, me, change-password.
2. Employee CRUD: create, get, list, update.
3. Onboarding workflows/tasks: create, list, get, update, task patch/create/list, progress, employee summary.
4. Orchestration: LangGraph-driven task blueprint generation, state sync, escalation events, persisted event log.
5. Notifications: list, unread count, mark read, mark all read; service-triggered notification generation.
6. RAG assistant: PDF upload, chunking, embeddings, search, grounded chat with citations, list/delete docs.
7. Analytics: dashboard aggregate metrics endpoint.

## Verified Constraints
1. Keep business logic in services, not in routers.
2. Use SQLAlchemy 2.0 style and async patterns.
3. Use Pydantic schemas for typed request/response contracts.
4. Use UUID primary keys and timezone-aware timestamps.
5. Keep AI client creation centralized in backend/app/ai/llm.py.
6. Use LCEL composition for chat chains (prompt | llm | parser).
7. Continue per-user vector collection strategy: user_{user_id}.

## Current Gaps (Do Not Pretend Implemented)
1. Backend websocket notifications endpoint is not present.
2. Email delivery is a placeholder (no provider integration).
3. Calendar sync integrations are not implemented.
4. SSO/MFA are not implemented.

## Frontend Standards For This Repo
1. Functional React components with TypeScript.
2. Prefer hooks and frontend/src/lib/api.ts for API access.
3. Preserve existing Tailwind UI patterns.
4. Keep page routes lazy-loaded when adding new route pages.

## Security Rules
1. Never hardcode secrets.
2. Do not log PII or tokens.
3. Validate user inputs and uploaded file types.
4. Preserve auth dependencies on protected endpoints.

## Testing and Validation Expectations
1. Update/add backend tests when changing service or API behavior.
2. Keep frontend build and TypeScript checks clean.
3. Verify migrations when model schema changes are introduced.

## Documentation Rule
When features are missing, mark as future scope explicitly. Do not document aspirational functionality as implemented.

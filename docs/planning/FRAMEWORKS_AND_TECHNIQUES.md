# Frameworks, Tools and Techniques Used

## Frontend

## React
Why used:
- componentized UI for dashboard-heavy workflows,
- mature routing ecosystem,
- strong compatibility with data-fetching libraries.

How it is used here:
- route-based pages for login, dashboard, workflows, analytics, notifications, AI assistant,
- shared layout/navigation and reusable UI primitives.

## TypeScript
Why used:
- safer API contracts across frontend/backend boundaries,
- better maintainability for a multi-page enterprise app.

How it is used here:
- typed models for users, employees, workflows, tasks, notifications, RAG responses,
- typed hooks and mutation/query contracts.

## Tailwind CSS
Why used:
- rapid, consistent UI implementation without large custom CSS overhead,
- easy responsive design and utility-driven styling.

How it is used here:
- all page/component styling is utility-class based,
- consistent card, layout, spacing, and state styling across modules.

## TanStack Query
Why used:
- robust server-state handling for enterprise dashboards,
- caching, invalidation, retries, polling, and mutation lifecycle support.

How it is used here:
- domain hooks encapsulate API reads/writes,
- mutation success handlers invalidate related queries,
- polling for notifications, workflow state, and analytics freshness.

## Zustand
Why used:
- lightweight global state for auth/UI concerns not suited for server cache,
- minimal boilerplate and straightforward updates.

How it is used here:
- auth store (user/loading/initialized),
- toast notifications,
- onboarding UI selection state.

## Backend

## FastAPI
Why used:
- high-performance async API framework,
- strong typing and automatic OpenAPI generation,
- dependency injection for auth/db access.

How it is used here:
- versioned API router (`/api/v1`),
- endpoint modules by domain,
- startup DB diagnostics and health endpoints.

## SQLAlchemy (Async)
Why used:
- mature ORM with async support,
- explicit model mapping and transaction control,
- portable across local PostgreSQL and managed providers.

How it is used here:
- SQLAlchemy 2.0-style async sessions,
- model-first schema with UUID keys and timestamps,
- service-layer queries and updates.

## Alembic
Why used:
- controlled schema evolution and reproducible DB setup,
- migration history for team and deployment consistency.

How it is used here:
- migration chain for base tables, datetime corrections, orchestration events, and notifications,
- env-aware DB URL resolution for migration runtime.

## JWT Authentication
Why used:
- stateless auth with role claims,
- suitable for API + SPA architecture.

How it is used here:
- JWT generated on login,
- token stored in `httpOnly` cookie,
- dependency-based guards for authenticated/admin routes.

## AI Stack

## LangChain
Why used:
- composable abstractions for prompts, models, and parsers,
- fast implementation of grounded QA pipelines.

How it is used here:
- LCEL composition (`prompt | llm | parser`),
- chat history memory integration for assistant continuity.

## LangGraph
Why used:
- deterministic multi-step state workflow orchestration,
- clean representation of onboarding lifecycle transitions.

How it is used here:
- graph nodes for each onboarding phase,
- derived state/progress/escalations,
- integration into orchestration service for persistence and notifications.

## LiteLLM
Why used:
- unified proxy to model providers,
- centralized model/embedding configuration.

How it is used here:
- `llm.py` centralizes chat and embedding clients,
- user context propagated for model call traceability.

## ChromaDB
Why used:
- practical vector store for RAG,
- easy local persistence plus HTTP mode support.

How it is used here:
- per-user collections (`user_{user_id}`),
- chunk embeddings + metadata storage,
- semantic retrieval used in assistant responses.

## DevOps and Runtime

## Docker
Why used:
- repeatable containerized environments,
- easier onboarding for local and demo deployments.

How it is used here:
- dedicated Dockerfiles for backend/frontend,
- containerized backend runtime and frontend dev server support.

## Docker Compose
Why used:
- orchestrates multi-service local stack quickly.

How it is used here:
- service topology includes PostgreSQL, ChromaDB, backend, and frontend,
- local volume mappings for persistence and uploads.

## Environment Configuration
Why used:
- secure, environment-specific runtime settings,
- avoids hardcoding secrets and infrastructure details.

How it is used here:
- pydantic-settings based config loading,
- DB/security/AI/chroma/upload settings sourced from env,
- secure-cookie behavior toggled by environment.

## Key Engineering Techniques Applied
- Layered architecture and service encapsulation.
- Role-based authorization at dependency layer.
- Async I/O for API and database operations.
- Query invalidation and polling for near-real-time UX.
- Event persistence for orchestration auditability.
- Retrieval-grounded AI responses with source citations.
- Per-user vector isolation for document retrieval boundaries.

## Verified Incomplete Areas (Not Claimed as Implemented)
- Backend WebSocket notifications endpoint is not implemented.
- Email delivery integration is placeholder only.
- Calendar sync integrations are not implemented.

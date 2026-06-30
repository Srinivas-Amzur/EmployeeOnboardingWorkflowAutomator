# Architecture Guide - Employee Onboarding Workflow Automator

This guide explains the architecture shown in [architecture.mmd](architecture.mmd).

## 1) Architecture Overview
The system is a layered web application with AI orchestration and retrieval-augmented assistance:

1. Frontend: React + TypeScript + Zustand + TanStack Query + TailwindCSS
2. Backend: FastAPI + Routers + Authentication Layer + Services + SQLAlchemy
3. AI Layer: LangGraph + LangChain + LiteLLM + RAG Engine
4. Storage: PostgreSQL (Supabase compatible) + ChromaDB + File Storage

The architecture separates presentation, API contracts, business logic, orchestration logic, and persistence concerns.

## 2) Frontend Components

## React UI
Role:
- Renders all screens for onboarding operations.

Implemented screens include:
- dashboard,
- onboarding list/detail,
- create employee,
- notifications,
- analytics,
- AI assistant,
- profile.

## TypeScript
Role:
- Enforces typed contracts for API payloads, app state, and component props.

## Zustand
Role:
- Holds lightweight client-side app state (auth session data, toast notifications, selected workflow state).

## TanStack Query
Role:
- Handles server-state fetching, caching, invalidation, polling, and mutation lifecycle.

## TailwindCSS
Role:
- Utility-first styling and responsive layouts for all pages/components.

## 3) Backend Components

## FastAPI
Role:
- Exposes REST APIs under `/api/v1` for auth, employees, onboarding, notifications, analytics, and rag.

## Routers
Role:
- Define endpoint handlers and request/response contracts.
- Delegate business logic to services.

## Authentication Layer
Role:
- JWT validation from httpOnly cookie.
- Admin guard (`admin`/`hr_admin`) for protected write operations.

## Service Layer
Role:
- Implements domain logic:
  - auth,
  - employee management,
  - onboarding workflows/tasks,
  - orchestration state sync,
  - notifications,
  - analytics,
  - RAG operations.

## SQLAlchemy
Role:
- Async ORM for models and queries against PostgreSQL/Supabase.

## 4) AI Layer Components

## LangGraph
Role:
- Deterministic workflow orchestration engine for onboarding lifecycle states.

## LangChain
Role:
- Chain composition for contextual chat and prompt handling (LCEL flow).

## LiteLLM
Role:
- Unified LLM/embedding gateway used by chat and vector operations.

## RAG Engine
Role:
- Handles document ingestion, chunking, embedding, retrieval, and grounded response generation.

## 5) Storage Components

## PostgreSQL (Supabase compatible)
Role:
- Source of truth for users, employees, workflows, tasks, notifications, and orchestration events.

## ChromaDB
Role:
- Vector store for semantically searchable onboarding knowledge chunks.

## File Storage
Role:
- Stores uploaded onboarding documents before/alongside indexing.

## 6) Request Flow A: Core Application Flow
Required flow represented in the diagram:

1. User -> React UI
2. React UI -> FastAPI APIs
3. FastAPI APIs -> Service Layer
4. Service Layer -> PostgreSQL

Detailed behavior:
- React pages invoke API client calls.
- FastAPI routers validate input and auth.
- Services execute business operations.
- SQLAlchemy persists and retrieves transactional data.

## 7) Request Flow B: AI Assistant Flow
Required flow represented in the diagram:

1. User -> AI Assistant
2. AI Assistant -> LangGraph
3. LangGraph -> LangChain
4. LangChain -> ChromaDB
5. ChromaDB -> LLM (through LiteLLM gateway)

Detailed behavior:
- User question enters assistant UI.
- Workflow context/orchestration can be included via LangGraph-driven logic.
- LangChain composes and executes retrieval-grounded chains.
- ChromaDB returns relevant chunks.
- LiteLLM-backed model generates final grounded response.

## 8) Operational Notes for Mentor Review
1. Layering is cleanly separated (UI, API, service, data, AI orchestration).
2. Business logic is service-centric, not router-centric.
3. AI path and transactional path are both explicit and traceable in diagram.
4. Diagram is presentation-ready and maps directly to implemented stack and modules.

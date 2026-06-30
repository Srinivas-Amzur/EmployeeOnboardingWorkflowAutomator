# DEPENDENCIES

## Primary Dependency Flow
Database -> Models -> Schemas -> Services -> LangGraph -> API Routes -> Frontend -> Analytics

## Layer Dependency Details
1. Database
- PostgreSQL tables managed by Alembic
- Chroma collections for semantic chunks
- Disk storage for uploaded docs

2. Models
- SQLAlchemy entities map database tables

3. Schemas
- Pydantic request/response validation around model-backed service I/O

4. Services
- Business logic, orchestration coordination, notification generation, analytics aggregation

5. LangGraph
- Invoked by OrchestrationService to derive tasks/state/events/escalations

6. API Routes
- Thin route handlers using dependency injection and service calls

7. Frontend
- API client + hooks + pages consume route contracts

8. Analytics
- Aggregation service consumes model data and powers dashboard views

## Mermaid: End-to-End Dependency
```mermaid
flowchart LR
  DB[(PostgreSQL)] --> M[SQLAlchemy Models]
  VDB[(ChromaDB)] --> VS[VectorStoreService]
  FS[(Disk Uploads)] --> DPS[DocumentProcessingService]

  M --> S[Services]
  SCH[Schemas] --> S
  S --> LG[LangGraph Orchestrator]
  LG --> S

  S --> API[FastAPI Routes]
  API --> FE[React + Hooks + API Client]
  S --> AN[AnalyticsService]
  AN --> API

  DPS --> RS[RAGService]
  VS --> RS
  RS --> API
```

## Mermaid: Backend Dependency Stack
```mermaid
flowchart TB
  subgraph API Layer
    A1[auth.py]
    A2[employees.py]
    A3[onboarding.py]
    A4[notifications.py]
    A5[rag.py]
    A6[analytics.py]
  end

  subgraph Service Layer
    S1[AuthService]
    S2[EmployeeService]
    S3[OnboardingService]
    S4[OrchestrationService]
    S5[NotificationService]
    S6[RAGService]
    S7[AnalyticsService]
  end

  subgraph Data Layer
    D1[SQLAlchemy Models]
    D2[PostgreSQL]
    D3[Alembic Migrations]
  end

  subgraph AI Layer
    AI1[llm.py]
    AI2[orchestrator.py]
    AI3[rag_chain.py]
    AI4[vector_store.py]
  end

  A1 --> S1
  A2 --> S2
  A3 --> S3
  A3 --> S4
  A4 --> S5
  A5 --> S6
  A6 --> S7

  S2 --> S4
  S3 --> S4
  S3 --> S5
  S6 --> S5
  S4 --> AI2
  S6 --> AI1
  S6 --> AI3
  S6 --> AI4

  S1 --> D1
  S2 --> D1
  S3 --> D1
  S4 --> D1
  S5 --> D1
  S7 --> D1
  D1 --> D2
  D3 --> D2
```

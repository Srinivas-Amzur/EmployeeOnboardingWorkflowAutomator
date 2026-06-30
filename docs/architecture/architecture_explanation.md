# AI-Powered Employee Onboarding Workflow Automator
## Architecture Explanation — Capstone Presentation Reference

---

## System Overview

The AI-Powered Employee Onboarding Workflow Automator is a full-stack enterprise application that uses LangGraph-based AI agents to automate, coordinate, and intelligently manage the entire employee onboarding lifecycle — from first-day task assignment to document distribution and IT provisioning.

The system reduces manual HR overhead, ensures no onboarding step is missed, and provides an AI assistant that employees and managers can query in natural language to get contextual answers about policies, processes, and their specific onboarding status.

---

## Layer-by-Layer Architecture Walkthrough

### 1. Users (4 Roles)
The system supports four distinct roles enforced through RBAC:
- **HR Admin** — creates and configures onboarding workflows, manages employee records
- **IT Admin** — receives provisioning tasks, manages system access
- **Manager** — monitors their team's onboarding progress
- **Employee** — accesses their personal onboarding dashboard and AI assistant

All roles share the same frontend but see role-filtered data and controls.

---

### 2. Frontend Layer
**Technology:** React 18 · TypeScript · Tailwind CSS · Zustand · TanStack Query

The SPA is delivered via **CloudFront CDN** and communicates with the backend exclusively through REST APIs secured with JWT HttpOnly cookies.

Key modules:
- **Dashboard** — role-specific summary of active onboarding workflows and pending tasks
- **Employee Onboarding** — workflow creation wizard for HR admins
- **Task Tracking** — real-time Kanban-style task board with status updates
- **AI Assistant** — chat interface powered by LangGraph; supports contextual Q&A over company documents
- **Document Management** — upload policy docs, role handbooks; triggers the RAG pipeline
- **Analytics** — onboarding completion rates, task delay metrics, time-to-productivity trends
- **Notifications** — real-time in-app notification feed

TanStack Query handles server state, caching, and optimistic updates. Zustand manages lightweight client-side UI state (drawer open/close, filters, selected workflow).

---

### 3. API Layer
**Technology:** FastAPI · Python 3.11 · Uvicorn · Pydantic v2

FastAPI serves as the single entry point for all client interactions. Every request passes through two middleware layers:

**Authentication:** JWT stored in HttpOnly cookies (prevents XSS token theft). On every request the JWT is verified and the user identity is extracted.

**Authorization:** RBAC middleware maps the user's role (HR Admin, IT Admin, Manager, Employee) to a permission set. Role-restricted endpoints return 403 if the role lacks access.

Routers handle: employee management, workflow CRUD, task management, document uploads, analytics queries, and AI chat.

---

### 4. Service Layer
The service layer contains pure business logic, decoupled from HTTP concerns:

| Service | Responsibility |
|---|---|
| Employee Service | Create/update employee records, role assignments |
| Workflow Service | Instantiate onboarding templates, track completion |
| Notification Service | Determine channel and trigger email / in-app events |
| Document Service | Receive uploads, hand off to RAG pipeline |
| Analytics Service | Aggregate metrics, compute SLAs |
| AI Assistant Service | Bridge to LangGraph agent, manage conversation history |

---

### 5. AI Orchestration Layer
**Technology:** LangGraph · LangChain LCEL

LangGraph orchestrates a **stateful multi-step workflow agent** that executes the onboarding process as a directed graph of nodes:

```
Create Workflow → Assign Tasks → IT Provisioning → Schedule Meetings
     → Document Distribution → Send Notifications → Mark Complete
```

Each node is a LangChain LCEL chain that can call tools (database writes, email sends, API calls to IT systems), query the RAG layer for context, and decide whether to proceed or pause for human approval.

LangGraph's state checkpointing allows workflows to resume after interruptions (e.g. manager approval required before IT provisioning).

---

### 6. LLM Gateway — LiteLLM Proxy
LiteLLM acts as a **unified proxy** in front of all LLM providers, providing:

- **Model routing** — route AI assistant queries to GPT-4o, Gemini 2.5 Flash, or fallback models based on availability and cost thresholds
- **Cost control** — per-model spending limits; automatic fallback when budget is exceeded
- **Observability** — logs every LLM call with token counts, latency, model used, and cost
- **Retry logic** — handles transient provider failures transparently

This ensures the application is not locked to a single provider and can adapt as model pricing changes.

---

### 7. RAG Layer — ChromaDB
The RAG pipeline enables the AI assistant to answer questions grounded in company-specific documents (HR policies, IT onboarding guides, benefits handbooks):

**Ingestion pipeline:**
1. HR Admin uploads a document via Document Management UI
2. Document Service extracts text, splits into 512-token overlapping chunks
3. Embeddings are created via the embedding model (OpenAI or local)
4. Chunks + embeddings are stored in ChromaDB with metadata (document ID, page, role access level)

**Retrieval pipeline (per AI query):**
1. User's question is embedded
2. ChromaDB performs cosine similarity search, returning top-K relevant chunks
3. Chunks are injected into the LLM system prompt as context
4. The LLM generates a grounded, cited response

---

### 8. Data Layer — PostgreSQL
All persistent application state lives in PostgreSQL (AWS RDS):

| Table | Purpose |
|---|---|
| users | Authentication identities and role assignments |
| employees | HR profile data, department, manager, start date |
| onboarding_workflows | Workflow templates and active instances |
| onboarding_tasks | Individual tasks within a workflow, assignee, status, due date |
| notifications | Notification log with channel, recipient, trigger event |
| uploaded_documents | Document metadata, S3 path, processing status |
| audit_logs | Immutable log of every state-changing action |

The audit_logs table records actor, action, timestamp, and diff for compliance.

---

### 9. Notification Layer
The Notification Service fans out events to channels based on user preferences and event type:

| Trigger Event | Default Channel |
|---|---|
| Workflow Started | Email + In-App |
| Task Assigned | Email + In-App |
| Task Completed | In-App |
| Delayed Task | Email + Manager In-App |
| Workflow Completed | Email + In-App |

Email delivery uses an SMTP provider (AWS SES). In-app notifications use server-sent events (SSE) for real-time push to the React frontend.

---

### 10. Security Architecture
- **Transport:** HTTPS everywhere; CloudFront enforces TLS 1.2+
- **Authentication:** JWT with 15-minute access tokens in HttpOnly cookies; refresh token rotation
- **Authorization:** RBAC enforced at API middleware level on every endpoint
- **Secrets:** All API keys and DB credentials stored in AWS Secrets Manager; injected as environment variables at container startup
- **Data encryption:** RDS encrypted at rest (AES-256); S3 SSE-S3; ChromaDB volume encrypted
- **Audit:** Every CREATE/UPDATE/DELETE action logged to the audit_logs table with actor identity

---

## AWS Deployment Architecture

```
Internet
    │
    ▼
CloudFront (Edge CDN)
    │  ← React SPA served from S3 origin
    │  ← API requests forwarded to ALB
    ▼
Application Load Balancer (HTTPS 443)
    │
    ▼
ECS Fargate Private Subnet (Auto-Scaling)
    ├── FastAPI App Containers (×N)
    ├── LangGraph Orchestrator Containers (×N)
    ├── LiteLLM Proxy Container
    └── ChromaDB Container
    │
    ▼
Data Subnet
    ├── RDS PostgreSQL (Multi-AZ, automated backups)
    ├── S3 Buckets (documents, frontend assets)
    └── Secrets Manager (API keys, DB credentials)

Monitoring:
    ├── CloudWatch (logs, metrics, alarms)
    └── Prometheus + Grafana (APM dashboards)

CI/CD:
    └── GitHub Actions → Docker Build → Push to ECR → ECS Rolling Deploy
```

**Scaling strategy:** ECS Fargate auto-scales FastAPI containers based on CPU/memory. The stateless API design means any container can handle any request. LangGraph state is persisted in PostgreSQL (not in-memory), so workflow resumption works across container restarts.

---

## Key Design Decisions

1. **LangGraph over raw LangChain:** LangGraph's stateful, checkpointable graph model is essential for multi-step onboarding workflows that may pause for human approval and resume hours later.

2. **LiteLLM Proxy as a gateway:** Abstracts provider coupling and enables cost observability from day one — critical for a production AI system.

3. **RAG over fine-tuning:** Company documents change frequently; RAG allows real-time document updates without model retraining.

4. **FastAPI + Pydantic v2:** Type-safe request/response validation, auto-generated OpenAPI docs, and async support for non-blocking I/O under concurrent load.

5. **JWT HttpOnly cookies over localStorage:** Prevents XSS-based token theft, the most common web auth vulnerability.

6. **ECS Fargate over EC2:** No server management overhead; scales to zero during off-hours; pay-per-use.

---

*Generated for capstone technical review — AI-Powered Employee Onboarding Workflow Automator*

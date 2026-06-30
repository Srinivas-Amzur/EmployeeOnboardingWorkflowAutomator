# Backend Architecture

# Backend Stack

- FastAPI
- Python 3.11
- SQLAlchemy 2.0
- PostgreSQL
- LangChain
- LangGraph

---

# Backend Structure

backend/app/

- api/
- services/
- models/
- schemas/
- ai/
- db/
- core/

---

# Architecture Pattern

router
↓
service
↓
model/schema

No business logic inside routers.

---

# API Layer

Responsibilities:
- request parsing
- auth validation
- response formatting

---

# Service Layer

Responsibilities:
- onboarding workflows
- AI orchestration
- task processing
- notifications

---

# Database Layer

Technology:
SQLAlchemy 2.0

Rules:
- UUID primary keys
- timezone-aware timestamps
- Alembic migrations only

---

# AI Layer

Modules:
- llm.py
- chains/
- prompts/
- rag/
- memory/

---

# Authentication

Uses:
- JWT
- httpOnly cookies
- bcrypt passwords

---

# File Upload Handling

Files:
- stored on disk

Metadata:
- stored in PostgreSQL

---

# Error Handling

Structured errors only:

{
  "error": "validation_error",
  "message": "Invalid request"
}

---

# Testing

Backend Testing:
- pytest
- pytest-asyncio
- httpx.AsyncClient
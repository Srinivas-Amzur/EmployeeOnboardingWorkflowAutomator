# Architecture Documentation

# Application Architecture

The Employee Onboarding Workflow Automator follows a modular enterprise architecture.

---

# High-Level Architecture

Frontend (React)
↓
FastAPI Backend
↓
Service Layer
↓
AI Layer + Database Layer
↓
PostgreSQL + ChromaDB + LiteLLM

---

# Frontend Architecture

## Pages
- Login
- Dashboard
- Onboarding
- Notifications
- Analytics
- AI Assistant

## Components
Reusable UI modules:
- onboarding cards
- task tables
- progress trackers
- notification panels

## Hooks
Custom hooks:
- useAuth
- useOnboarding
- useNotifications

---

# Backend Architecture

## API Layer
Responsibilities:
- request validation
- auth handling
- response formatting

No business logic allowed.

---

## Service Layer
Responsibilities:
- onboarding logic
- task orchestration
- AI coordination
- notification processing

---

## AI Layer
Modules:
- llm.py
- chains/
- rag/
- prompts/
- memory/

---

# AI Architecture

## LiteLLM Proxy

ALL AI requests route through:
https://litellm.amzur.com

Supported Models:
- gemini/gemini-2.5-flash
- gpt-4o

---

# LangGraph Workflow

Workflow Nodes:
- create_workflow
- assign_tasks
- provisioning
- schedule_meetings
- document_distribution
- notifications
- completion

---

# RAG Architecture

## Document Pipeline
1. upload document
2. chunk content
3. create embeddings
4. store in ChromaDB
5. retrieve semantically
6. generate AI response

---

# Database Architecture

Core Tables:
- users
- employees
- onboarding_workflows
- onboarding_tasks
- notifications
- uploaded_documents
- audit_logs

---

# Notification Architecture

Channels:
- email
- in-app notifications

Triggers:
- onboarding state changes
- task completion
- delays

---

# Security Architecture

## Authentication
JWT httpOnly cookies

## Authorization
RBAC roles:
- HR
- IT
- Manager
- Employee

---

# File Upload Architecture

Files stored:
UPLOAD_DIR/

Metadata stored:
PostgreSQL

Vectorized content:
ChromaDB

---

# Deployment Architecture

## Development
Docker Compose

## Production
Recommended:
- Kubernetes
- AWS ECS
- NGINX reverse proxy

---

# Recommended Infrastructure

## Frontend
- Vercel
OR
- NGINX container

## Backend
- FastAPI container

## Database
- PostgreSQL

## Vector DB
- ChromaDB persistent volume

---

# Non-Functional Requirements

The system must support:
- scalability
- modularity
- maintainability
- observability
- secure access
- auditability
# Project Scaffold Implementation Guide

## Overview

This document provides step-by-step instructions to complete the Employee Onboarding Workflow Automator project scaffold and prepare for development.

## Phase 1: Initial Setup (30 minutes)

### Step 1.1: Environment Configuration

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your configuration
# Critical settings to update:
# - JWT_SECRET_KEY: Generate a strong secret
# - LITELLM_PROXY_URL: Set to https://litellm.amzur.com
# - LITELLM_API_KEY: Add your API key
# - DATABASE_URL: Verify PostgreSQL connection string

# Generate JWT secret (macOS/Linux):
python -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT secret (Windows PowerShell):
[Convert]::ToBase64String($(Get-Random -InputObject (0..255) -Count 32))
```

### Step 1.2: Git Initialization

```bash
# Initialize git repository
git init

# Add initial commit
git add .
git commit -m "feat: initial project scaffold"
```

## Phase 2: Backend Setup (45 minutes)

### Step 2.1: Create Python Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Verify activation (should show venv path)
which python  # or: where python
```

### Step 2.2: Install Backend Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify FastAPI installation
python -c "import fastapi; print(fastapi.__version__)"

# Verify SQLAlchemy
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

### Step 2.3: Initialize Database

```bash
# Create database (assuming PostgreSQL is running)
# Option 1: Using psql
psql -U postgres -c "CREATE DATABASE onboarding_db;"

# Option 2: Using Docker PostgreSQL
docker run --name postgres_onboarding -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=onboarding_db -p 5432:5432 -d postgres:16-alpine

# Initialize Alembic (one-time setup)
alembic init -t async app/db/migrations

# Create initial migration
cd ..
alembic revision --autogenerate -m "Initial schema creation"

# Apply migrations
alembic upgrade head

# Verify database tables
psql -U postgres -d onboarding_db -c "\dt"
```

### Step 2.4: Test Backend

```bash
# From backend directory
python main.py

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Visit API docs
open http://localhost:8000/docs  # or http://localhost:8000/redoc
```

## Phase 3: Frontend Setup (30 minutes)

### Step 3.1: Install Node Dependencies

```bash
cd frontend

# Install dependencies
npm install

# Verify Node version (requires 18+)
node --version
```

### Step 3.2: Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Verify API URL
cat .env
# Should contain: VITE_API_URL=http://localhost:8000/api/v1
```

### Step 3.3: Test Frontend

```bash
# Start development server
npm run dev

# Frontend available at: http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview
```

## Phase 4: Docker Setup (20 minutes)

### Step 4.1: Docker Compose Configuration

```bash
# From project root

# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Step 4.2: Initialize Database in Docker

```bash
# Apply migrations in Docker
docker-compose exec backend alembic upgrade head

# Create test user (optional)
docker-compose exec backend python -c "
from app.core.security import hash_password
from app.models import User
from app.db.session import AsyncSessionLocal
import asyncio

async def create_user():
    async with AsyncSessionLocal() as db:
        user = User(
            name='Test Admin',
            email='admin@example.com',
            hashed_password=hash_password('password123'),
            role='admin'
        )
        db.add(user)
        await db.commit()

asyncio.run(create_user())
"
```

## Phase 5: Integration Testing (15 minutes)

### Step 5.1: Test Authentication Flow

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# Create employee
curl -X POST http://localhost:8000/api/v1/employees \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<token-from-login>" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "department": "Engineering",
    "designation": "Software Engineer",
    "joining_date": "2026-06-01"
  }'
```

### Step 5.2: Test AI Integration

```bash
# Test LLM connection
python -c "
from app.ai import get_fast_llm
from app.core.logging import setup_logging

setup_logging()

llm = get_fast_llm()
print('LLM Model:', llm.model_name)
print('API Key configured:', bool(llm.api_key))
"
```

### Step 5.3: Test RAG System

```bash
# Verify ChromaDB connection
python -c "
from app.ai import get_chromadb_client

client = get_chromadb_client()
print('Connected to ChromaDB')
"
```

## Phase 6: Development Workflow Setup (15 minutes)

### Step 6.1: Install Development Tools

```bash
# Backend development tools
pip install black ruff mypy

# Frontend development tools
npm install -D eslint @typescript-eslint/eslint-plugin

# Pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Step 6.2: Code Formatting

```bash
# Backend formatting
black backend/app --line-length 100

# Backend linting
ruff check backend/app --fix

# Frontend formatting
npm run lint
```

## Phase 7: First Feature Implementation

### Step 7.1: Create Service Layer

```bash
# Create onboarding service (backend/app/services/onboarding.py)
# Implement:
# - create_workflow()
# - get_workflow_progress()
# - update_workflow_state()
```

### Step 7.2: Create API Endpoints

```bash
# Expand endpoints in backend/app/api/v1/endpoints/
# Add:
# - GET /onboarding/workflows - list workflows
# - POST /onboarding/workflows/{id}/tasks - add task
# - GET /onboarding/workflows/{id}/progress - get progress
```

### Step 7.3: Create Frontend Pages

```bash
# Create pages in frontend/src/pages/
# Add:
# - OnboardingListPage.tsx
# - OnboardingDetailPage.tsx
# - AnalyticsDashboard.tsx
```

## Troubleshooting

### Database Issues

```bash
# Reset database (WARNING: destructive!)
psql -U postgres -d onboarding_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Backend Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### Frontend Build Issues

```bash
# Clear node modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

### Docker Issues

```bash
# Clean all containers and images
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Next Steps

1. **Complete Service Layer** - Implement business logic services
2. **Add Error Handling** - Comprehensive error handling throughout
3. **Implement RAG** - Complete document ingestion and search
4. **Add Notifications** - Email and in-app notifications
5. **Build Analytics** - Dashboard and reporting features
6. **Add Tests** - Unit and integration tests
7. **Setup CI/CD** - GitHub Actions pipeline
8. **Deploy** - Deploy to production environment

## Architecture Reminders

### Backend Rules (MANDATORY)
- ✅ async FastAPI routes only
- ✅ router → service → schema → model architecture
- ✅ NO business logic in route handlers
- ✅ UUID primary keys
- ✅ Timezone-aware timestamps
- ✅ Pydantic validation on all inputs

### Frontend Rules (MANDATORY)
- ✅ Functional components only
- ✅ Strict TypeScript
- ✅ TanStack Query for server state
- ✅ Zustand for app state
- ✅ Tailwind CSS only

### AI Rules (MANDATORY)
- ✅ ALL AI calls through LiteLLM only
- ✅ NO direct OpenAI/Gemini calls
- ✅ LCEL syntax only
- ✅ LangGraph for orchestration
- ✅ include user=email on AI calls

## Quick Reference Commands

```bash
# Backend
cd backend
source venv/bin/activate
python main.py

# Frontend
cd frontend
npm run dev

# Docker
docker-compose up -d
docker-compose logs -f

# Database
alembic revision --autogenerate -m "message"
alembic upgrade head

# Testing
pytest
npm run test
```

## Support

Refer to project documentation:
- Architecture: `docs/ARCHITECTURE.md`
- Database: `docs/DB_SCHEMA.md`
- API: `docs/API_CONTRACTS.md`
- AI: `docs/AI_ORCHESTRATION.md`
- RAG: `docs/RAG_ARCHITECTURE.md`
- Security: `docs/SECURITY.md`
- Deployment: `docs/DEPLOYMENT.md`

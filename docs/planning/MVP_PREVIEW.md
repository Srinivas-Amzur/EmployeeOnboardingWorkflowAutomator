# MVP_PREVIEW

## What A User Can Do After 2 Weeks
1. Sign in and manage session securely.
2. Create employee onboarding records.
3. Create and track onboarding workflows/tasks.
4. View workflow progress, events, and stage transitions.
5. Receive and manage in-app onboarding notifications.
6. Upload onboarding PDFs for RAG indexing.
7. Ask AI assistant onboarding questions with cited sources.
8. View operational analytics dashboards.

## Screens Available
1. Login
2. Dashboard
3. Create Employee
4. Onboarding Workflow List
5. Onboarding Workflow Detail
6. Notifications
7. Analytics
8. AI Assistant
9. Profile

## APIs Available
1. Health
- GET /health
- GET /health/db

2. Auth
- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- POST /api/v1/auth/register
- GET /api/v1/auth/me
- PATCH /api/v1/auth/change-password

3. Employees
- POST /api/v1/employees
- GET /api/v1/employees
- GET /api/v1/employees/{employee_id}
- PUT /api/v1/employees/{employee_id}

4. Onboarding
- POST /api/v1/onboarding/workflows
- GET /api/v1/onboarding/workflows
- GET /api/v1/onboarding/workflows/{workflow_id}
- PUT /api/v1/onboarding/workflows/{workflow_id}
- GET /api/v1/onboarding/workflows/{workflow_id}/progress
- GET /api/v1/onboarding/workflows/{workflow_id}/orchestration
- GET /api/v1/onboarding/workflows/{workflow_id}/events
- POST /api/v1/onboarding/workflows/{workflow_id}/tasks
- GET /api/v1/onboarding/workflows/{workflow_id}/tasks
- PATCH /api/v1/onboarding/tasks/{task_id}
- GET /api/v1/onboarding/employees/{employee_id}/summary

5. Notifications
- GET /api/v1/notifications
- GET /api/v1/notifications/unread-count
- PATCH /api/v1/notifications/{notification_id}/read
- PATCH /api/v1/notifications/read-all

6. RAG
- POST /api/v1/rag/documents/upload
- POST /api/v1/rag/chat
- POST /api/v1/rag/search
- GET /api/v1/rag/documents
- DELETE /api/v1/rag/documents/{document_id}

7. Analytics
- GET /api/v1/analytics/dashboard

## AI Capabilities Available
1. LangGraph onboarding orchestration with deterministic workflow state logic.
2. Automatic task blueprint generation by onboarding stage.
3. Escalation event generation for overdue tasks.
4. PDF-based RAG ingestion and semantic retrieval per user collection.
5. LCEL chat responses with source citation payloads.

## Demo Flow
1. Login as admin/hr_admin user.
2. Create a new employee (auto workflow creation optional from UI).
3. Open Onboarding list and inspect generated workflow/tasks.
4. Update task statuses and observe workflow progress/state changes.
5. Open Notifications and mark items read.
6. Upload onboarding policy PDF in AI Assistant.
7. Ask policy question and show cited grounded response.
8. Open Analytics dashboard and review aggregate metrics.

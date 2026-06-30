# API Contracts (Implementation-Verified)

This document reflects the currently implemented backend API behavior.

## Response Envelope

Most endpoints return data in a wrapper response:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

Validation and auth failures follow FastAPI error semantics (for example `422`, `401`, `403`, `404`) and are not wrapped in the same envelope.

## Authentication

Base path: `/api/v1/auth`

- `POST /register`
- `POST /login`
- `POST /logout`
- `GET /me`
- `POST /change-password`

Authentication is JWT-based and stored in HTTP-only cookies.

## Employees

Base path: `/api/v1/employees`

- `POST /` create employee
- `GET /{employee_id}` get employee details
- `GET /` list employees
- `PUT /{employee_id}` update employee

## Onboarding Workflows

Base path: `/api/v1/onboarding`

- `POST /` create workflow
- `GET /{workflow_id}` get workflow
- `GET /` list workflows
- `PUT /{workflow_id}` update workflow
- `GET /{workflow_id}/progress` workflow progress
- `POST /{workflow_id}/tasks` create task
- `GET /{workflow_id}/tasks` list tasks
- `PATCH /tasks/{task_id}` patch task
- `GET /employee/{employee_id}/summary` employee onboarding summary

## Meetings

Base path: `/api/v1/meetings`

- `POST /` create meeting
- `GET /{meeting_id}` get meeting
- `GET /` list meetings
- `PUT /{meeting_id}` update meeting
- `PATCH /{meeting_id}/status` update meeting status

## Notifications

Base path: `/api/v1/notifications`

- `GET /` list notifications
- `GET /unread-count` unread notification count
- `PATCH /{notification_id}/read` mark one as read
- `PATCH /mark-all-read` mark all as read

## Analytics

Base path: `/api/v1/analytics`

- `GET /dashboard` dashboard aggregates

## RAG and Chat

Base path: `/api/v1/rag`

- `POST /upload` upload and index PDF
- `POST /query` similarity search query
- `POST /chat` grounded chat with citations
- `GET /docs` list uploaded docs
- `DELETE /docs/{doc_id}` delete indexed doc

Important: chat is implemented under `/rag/chat` (not `/ai/chat`).

## Orchestration

Base path: `/api/v1/orchestration`

- `POST /workflows/{workflow_id}/generate-blueprint`
- `POST /workflows/{workflow_id}/sync-state`
- `POST /workflows/{workflow_id}/escalate`
- `GET /workflows/{workflow_id}/events`

## Notes on Role Scoping

- Employee-role users are restricted to self-scoped data for employee, workflow, and meeting access paths.
- Admin/HR/manager roles can access broader organizational data where route logic permits.

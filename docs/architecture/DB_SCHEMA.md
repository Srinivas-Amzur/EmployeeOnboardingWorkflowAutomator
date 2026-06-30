# Database Schema (Implementation-Verified)

This schema summary reflects the SQLAlchemy models currently implemented in the backend.

## Base Conventions

- UUID primary keys (`id`)
- Timestamp mixin fields (`created_at`, `updated_at`)
- Timezone-aware datetimes for workflow/task/meeting scheduling where applicable

## users

Stores authenticated platform users.

Representative fields:
- `id` (UUID, PK)
- `email` (unique)
- `hashed_password`
- `full_name`
- `role` (employee, manager, hr, admin)
- `is_active`
- timestamps

## employees

Employee profile and onboarding ownership.

Fields:
- `id` (UUID, PK)
- `first_name`
- `last_name`
- `email` (unique, indexed)
- `department`
- `designation`
- `manager_id` (FK -> users.id)
- `joining_date` (date)
- `onboarding_status`
- timestamps

## onboarding_workflows

Workflow execution state per employee.

Fields:
- `id` (UUID, PK)
- `employee_id` (FK -> employees.id)
- `current_state`
- `completion_percentage`
- `started_at` (tz-aware datetime)
- `completed_at` (nullable tz-aware datetime)
- timestamps

## onboarding_tasks

Task items belonging to workflows.

Fields:
- `id` (UUID, PK)
- `workflow_id` (FK -> onboarding_workflows.id)
- `title`
- `description` (nullable)
- `assigned_to` (nullable FK -> users.id)
- `status`
- `priority`
- `due_date` (nullable tz-aware datetime)
- `completed_at` (nullable tz-aware datetime)
- timestamps

## onboarding_meetings

Meetings associated with onboarding workflows.

Fields:
- `id` (UUID, PK)
- `employee_id` (FK -> employees.id)
- `workflow_id` (FK -> onboarding_workflows.id)
- `created_by` (nullable FK -> users.id)
- `meeting_type`
- `title`
- `description` (nullable)
- `scheduled_for` (tz-aware datetime)
- `duration_minutes`
- `location` (nullable)
- `meeting_url` (nullable)
- `status`
- timestamps

## notifications

In-app notification records.

Representative fields:
- `id` (UUID, PK)
- `user_id` (FK -> users.id)
- `type`
- `title`
- `message`
- `is_read`
- timestamps

## documents

RAG document metadata and lifecycle flags.

Representative fields:
- `id` (UUID, PK)
- `user_id` (FK -> users.id)
- `filename`
- `content_type`
- `status`
- timestamps

## onboarding_orchestration_events

Persisted orchestration event log from LangGraph flows.

Fields:
- `id` (UUID, PK)
- `workflow_id` (FK -> onboarding_workflows.id, indexed)
- `employee_id` (FK -> employees.id, indexed)
- `event_type` (indexed)
- `status`
- `state_from` (nullable)
- `state_to` (nullable)
- `message`
- `payload` (JSON, nullable)
- timestamps

## Implementation Notes

- This document intentionally excludes aspirational entities that are not represented in current SQLAlchemy models.
- Actual migration state should be validated against Alembic history when planning schema changes.

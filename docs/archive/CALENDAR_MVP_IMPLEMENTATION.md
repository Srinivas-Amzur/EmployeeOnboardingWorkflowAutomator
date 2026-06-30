# CALENDAR MVP IMPLEMENTATION

Date: 2026-06-07
Scope: Internal onboarding meeting scheduling MVP (no external calendar provider)

## Objective

Implement an onboarding calendar scheduling MVP without Google Calendar integration.

## Delivered Components

### 1) Meeting Model

Added persistent meeting model:
- File: backend/app/models/meeting.py
- Table: onboarding_meetings
- Core fields:
  - employee_id
  - workflow_id
  - meeting_type (orientation, manager_introduction, team_onboarding, custom)
  - title, description
  - scheduled_for, duration_minutes
  - location, meeting_url
  - status (scheduled, completed, cancelled)
  - created_by, timestamps

Migration added:
- File: backend/app/db/migrations/versions/006_add_onboarding_meetings.py

### 2) Meeting CRUD API

Added full CRUD API under /meetings:
- POST /meetings
- GET /meetings
- GET /meetings/{meeting_id}
- PUT /meetings/{meeting_id}
- DELETE /meetings/{meeting_id}

Implementation files:
- backend/app/api/v1/endpoints/meetings.py
- backend/app/services/meeting.py
- backend/app/schemas/meeting.py

### 3) Schedule Required Onboarding Meetings

Added explicit scheduling endpoints:
- POST /meetings/workflows/{workflow_id}/schedule-orientation
- POST /meetings/workflows/{workflow_id}/schedule-manager-introduction
- POST /meetings/workflows/{workflow_id}/schedule-team-onboarding-session

Each endpoint:
- creates meeting record
- links meeting to employee/workflow
- emits orchestration timeline event
- triggers in-app notification flow
- updates workflow state to meetings_scheduled when appropriate

## Display Requirements Implemented

### Upcoming meetings
Displayed on:
- frontend/src/pages/DashboardPage.tsx

Behavior:
- queries upcoming meetings from backend
- shows title, status, scheduled datetime, workflow reference

### Employee meetings
Displayed on:
- frontend/src/pages/EmployeePortalPage.tsx

Behavior:
- queries employee-scoped meetings
- shows scheduled meeting count and list

### Workflow meetings
Displayed on:
- frontend/src/pages/OnboardingDetailPage.tsx

Behavior:
- queries workflow-scoped meetings
- shows status and schedule details
- includes one-click schedule actions for required meeting types

## Workflow Integration

Meeting scheduling is integrated with onboarding workflow by:
- persisting meeting records with workflow_id
- writing orchestration events (meeting_scheduled/meeting_updated/meeting_cancelled)
- transitioning workflow.current_state to meetings_scheduled when workflow is active
- generating notifications through existing notification service mapping

## Frontend Integration

Added new API client and hooks:
- frontend/src/lib/api.ts (meetingAPI)
- frontend/src/hooks/index.ts
  - useMeetings
  - useCreateMeeting
  - useUpdateMeeting
  - useDeleteMeeting
  - useScheduleWorkflowMeeting

Added new shared types:
- frontend/src/types/index.ts

## Explicit Non-Goal

Google Calendar integration is intentionally not implemented in this MVP.
All scheduling is internal and persisted in platform database only.

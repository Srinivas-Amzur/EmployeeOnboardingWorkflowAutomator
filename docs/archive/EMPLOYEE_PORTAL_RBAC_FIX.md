# EMPLOYEE PORTAL RBAC FIX

Date: 2026-06-07
Scope: Employee portal authorization model and self-service data access

## Problem

Employee portal relied on admin-only employee listing to resolve the current employee profile.

Observed risk:
- Employee users could not reliably load portal data without admin-level employee API usage.
- Several onboarding/meeting read endpoints accepted broad filters without strict self-scope enforcement.

## Requirements Addressed

Employee users can now access, without admin permissions:
- their profile
- their workflow
- their tasks
- their notifications
- their documents

And do not receive employee list access.

## Root Cause Analysis

1. Portal profile resolution
- Frontend used `GET /employees` list and matched by email.
- `GET /employees` is admin-protected.

2. Onboarding read access scope
- Non-admin users could call onboarding endpoints with arbitrary IDs/filters.
- Ownership checks were incomplete for some read/update paths.

3. Meetings read access scope
- Meeting list/get endpoints did not fully enforce self-scope for non-admin users.

## Implemented Fixes

### A) Dedicated self-profile endpoint
File: backend/app/api/v1/endpoints/employees.py

- Added `GET /employees/me` to fetch employee profile mapped to authenticated user email.
- Added non-admin guard on `GET /employees/{employee_id}` so users can only read their own profile.
- Kept employee list endpoint admin-only.

### B) Onboarding ownership enforcement
File: backend/app/api/v1/endpoints/onboarding.py

For non-admin users:
- `GET /onboarding/workflows` is forcibly scoped to current employee.
- Workflow ID endpoints now verify workflow ownership before returning:
  - workflow detail
  - progress
  - snapshot/orchestration
  - events
  - tasks
- Task patch path validates task->workflow ownership before update.
- Employee summary endpoint is restricted to self unless admin.

### C) Meeting ownership enforcement
File: backend/app/api/v1/endpoints/meetings.py

For non-admin users:
- Meeting list is scoped to current employee.
- Meeting get validates ownership.
- Workflow filter access validates workflow ownership.

### D) Frontend portal migration to self profile
Files:
- frontend/src/lib/api.ts
- frontend/src/hooks/index.ts
- frontend/src/pages/EmployeePortalPage.tsx

Changes:
- Added employee self-profile API method (`employeeAPI.me`).
- Added `useMyEmployee` hook.
- Employee portal now uses self-profile endpoint instead of admin employee list API.

## Security Outcome

- Employee users can access only their own onboarding domain data.
- Employee list remains admin-only.
- Portal no longer depends on admin endpoints.

## Notes

- Notifications and RAG document endpoints were already user-scoped and remain unchanged.

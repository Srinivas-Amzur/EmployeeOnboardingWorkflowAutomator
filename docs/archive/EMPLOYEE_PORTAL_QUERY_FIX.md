# EMPLOYEE PORTAL QUERY FIX

Date: 2026-06-07
Scope: Employee Portal workflow query validation and resilience

## Problem Statement

Employee Portal workflow query could send an invalid `limit=0` value when employee context was unresolved.

Backend contract enforces:
- `limit >= 1` for onboarding workflow list endpoint.

Risk:
- Potential `422 Unprocessable Entity` responses.
- Unclear UX when employee profile linkage is missing.

## Investigation

### 1. Current frontend query path
File: frontend/src/pages/EmployeePortalPage.tsx

Previous behavior:
- If employee matched current user email:
  - `useWorkflows({ employee_id, limit: 20 })`
- Else:
  - `useWorkflows({ limit: 0 })`

This directly introduced an invalid backend query parameter.

### 2. Hook behavior
File: frontend/src/hooks/index.ts

Previous `useWorkflows` hook:
- Always executed query.
- Did not support `enabled` gating.
- Passed params directly to API call.

### 3. Backend validation
File: backend/app/api/v1/endpoints/onboarding.py

`list_workflows` endpoint validates:
- `limit: Query(10, ge=1, le=100)`

Therefore, `limit=0` is invalid and can return 422.

## Fix Implemented

### A) Workflows hook hardening
File: frontend/src/hooks/index.ts

Changes:
1. Added optional `enabled` field to `useWorkflows` params.
2. Added param split:
   - `enabled` used only by React Query control.
   - only API-safe params sent to backend.
3. Query now respects `enabled` and can be disabled until employee context is available.

### B) Employee Portal query + fallback handling
File: frontend/src/pages/EmployeePortalPage.tsx

Changes:
1. Replaced invalid `limit: 0` path.
2. Added constant valid default:
   - `WORKFLOW_QUERY_LIMIT = 20`
3. Added query gating:
   - `enabled: !!myEmployee`
4. Added graceful fallback state when employee profile is missing/unavailable:
   - explicit empty state message for profile linkage issue.
5. Kept existing loading and no-workflow empty states, now with proper guard conditions.

## Guarantee After Fix

- Valid default limit is always used (`20`) when querying workflows.
- No `limit=0` requests are sent.
- Workflow query is disabled when employee context is absent.
- No 422 responses from this Employee Portal query path due to invalid limit.
- Loading and empty states remain clear and role-safe when no employee record is found.

## Files Modified

- frontend/src/hooks/index.ts
- frontend/src/pages/EmployeePortalPage.tsx

## Validation

- Type checks pass for modified files.
- Query logic now aligns with backend `limit >= 1` validation contract.

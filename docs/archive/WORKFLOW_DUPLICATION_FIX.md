# WORKFLOW DUPLICATION FIX

Date: 2026-06-07
Scope: Employee creation workflow duplication analysis and fix

## Problem Statement

Creating a new employee could generate duplicate onboarding workflows.

Expected behavior:
- One employee creation request should result in exactly one onboarding workflow.
- No duplicated analytics counts.
- No duplicated notification streams.
- No duplicated workflow records.

## Investigation

### 1. Employee creation API
- Endpoint: POST /employees
- File: backend/app/api/v1/endpoints/employees.py
- Behavior: delegates to EmployeeService.create_employee.

Conclusion:
- API itself does not create duplicate workflows directly.

### 2. Frontend Create Employee flow
- File: frontend/src/pages/CreateEmployeePage.tsx
- Previous behavior:
  - Called createEmployee.mutateAsync(payload)
  - Then called createWorkflow.mutateAsync(...) when auto_create_workflow was enabled.

Conclusion:
- Frontend performed a second explicit workflow creation after employee creation.

### 3. Backend employee service
- File: backend/app/services/employee.py
- Behavior:
  - create employee row
  - immediately calls OrchestrationService.orchestrate_for_employee(employee)

Conclusion:
- Backend already triggers onboarding orchestration on employee creation.

### 4. LangGraph orchestration trigger
- File: backend/app/services/orchestration.py
- Behavior:
  - orchestrate_for_employee uses _ensure_workflow(employee)
  - _ensure_workflow creates workflow when absent
  - orchestration generates tasks/events/notifications and updates workflow state

Conclusion:
- Employee creation path already guarantees one workflow initialization in orchestration.

## Root Cause

Duplicate workflow creation was caused by overlapping responsibilities:
- Backend employee service auto-orchestrates and creates workflow.
- Frontend Create Employee page also called onboarding workflow creation API explicitly.

## Fix Implemented

File changed:
- frontend/src/pages/CreateEmployeePage.tsx

Changes:
1. Removed useCreateOnboardingWorkflow hook usage from Create Employee page.
2. Removed explicit createWorkflow.mutateAsync(...) call after employee creation.
3. Removed auto_create_workflow toggle from form state and UI.
4. Added informational note that employee creation automatically triggers one workflow.
5. Simplified submit/loading/error handling to rely only on createEmployee mutation.
6. Added backend idempotency guard in onboarding workflow creation service:
  - OnboardingService.create_workflow now checks for an existing workflow for the employee and returns it instead of creating a duplicate record.

## Why This Fix Works

After fix:
- Frontend sends one request: create employee.
- Backend performs one orchestration trigger.
- Orchestration creates one workflow for that employee in this flow.

Result:
- No duplicate workflow row from frontend double-create path.
- No duplicate workflow row from repeated/direct onboarding workflow create API calls for the same employee.
- No duplicate analytics inflation from duplicated workflows.
- No duplicate notifications/events from duplicate workflow creation path.

## Validation Checklist

- [x] Frontend create flow no longer calls onboarding create workflow API.
- [x] Backend employee creation still triggers orchestration.
- [x] Orchestration still initializes onboarding workflow.
- [x] Single-source-of-truth workflow creation is now backend employee service.
- [x] Backend onboarding workflow create API path is idempotent per employee and does not create duplicate workflow records.

## Recommended Follow-up Hardening

Optional deeper protection if strict one-workflow-per-employee must be guaranteed at DB level:
- Add a database uniqueness constraint policy for active workflow records by employee_id.

Current fix already prevents duplication in the known frontend and service API paths.

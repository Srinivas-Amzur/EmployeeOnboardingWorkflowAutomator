# FINAL CAPSTONE GAP ANALYSIS

Date: 2026-06-07
Project: Employee Onboarding Workflow Automator
Assessment Type: Final readiness review (read-only)

## Executive Summary

Overall readiness is strong for core onboarding orchestration, task tracking, notifications, analytics, and RAG assistant flows.

Current readiness score: 8.1 / 10

The codebase is functionally rich, but there are critical submission risks:
- workflow duplication risk at employee creation
- employee portal role/data-access mismatch
- lifecycle pause and resume actions do not persist actual workflow status changes
- calendar feature remains non-integrated (task placeholder only)
- audit logs are globally visible to any authenticated user

These should be addressed before final capstone submission if strict scope validation is expected.

---

## Scope Validation Against Required Features

### 1. New Hire Data Feature
Status: Partially complete
- Implemented backend CRUD for employee data.
- Frontend supports create flow.
- Gap: no dedicated employee management page for listing/editing employee profiles in the UI (beyond workflow views and create form).

### 2. IT Provisioning Feature
Status: Partially complete
- Implemented as orchestrated tasks in provisioning stage.
- Gap: no real provisioning integrations or execution adapters (only task generation/tracking).

### 3. Calendar Feature
Status: Incomplete
- Workflow has meetings_scheduled state and meeting-related tasks.
- No meetings domain model/API/integration layer exists.

### 4. Documentation Feature
Status: Complete (MVP level)
- Document upload, chunking, indexing, retrieval, chat citations, list/delete are implemented.

### 5. Notification Feature
Status: Complete (MVP level)
- In-app notifications, unread count, mark read/all read are implemented.
- Gap: websocket delivery remains optional and backend WS endpoint is not implemented.

### 6. Central Workflow Orchestrator
Status: Complete (MVP level)
- LangGraph orchestration, task blueprinting, state derivation, escalations, event persistence implemented.

---

## Findings By Priority

## P0 Must Fix Before Submission

1. Duplicate workflow creation path can create multiple workflows for one employee
- Impact: broken business flow, duplicate workflow records, incorrect analytics, confusing demo behavior.
- Evidence:
  - frontend/src/pages/CreateEmployeePage.tsx line 96 triggers additional workflow creation after employee creation when auto_create_workflow is true.
  - backend/app/services/employee.py line 38 already runs orchestrate_for_employee during employee creation.

2. Employee portal is incompatible with employee role access
- Impact: intended employee self-service page can fail for non-admin users.
- Evidence:
  - frontend/src/pages/EmployeePortalPage.tsx line 40 calls useEmployees(0, 500).
  - backend/app/api/v1/endpoints/employees.py line 51 protects list_employees with get_current_admin_user.

3. Employee portal sends invalid workflow query when no employee is resolved
- Impact: potential 422 errors and unstable page behavior.
- Evidence:
  - frontend/src/pages/EmployeePortalPage.tsx line 50 uses { limit: 0 } when no employee is found.
  - backend onboarding list endpoint enforces limit >= 1.

4. Pause and resume lifecycle actions do not persist a concrete workflow status change
- Impact: requirement says persist status changes, but pause/resume only create events and messages.
- Evidence:
  - backend/app/services/onboarding.py line 355 pause branch does not update workflow.current_state.
  - backend/app/services/onboarding.py line 358 resume branch does not update workflow.current_state.
  - Only complete action updates state at backend/app/services/onboarding.py line 366.

5. Calendar feature is still not implemented beyond task placeholders
- Impact: required project-scope feature remains missing.
- Evidence:
  - backend/app/ai/orchestrator.py defines meetings_scheduled tasks only.
  - backend/app/models/__init__.py has no Meeting model export.
  - backend/app/api/v1/__init__.py has no calendar router.

6. Audit logs endpoint exposes system-wide audit data to any authenticated user
- Impact: security and privacy risk; employees can access broad operational logs.
- Evidence:
  - backend/app/api/v1/endpoints/audit.py line 23 uses get_current_user instead of admin-level dependency.

## P1 Recommended

1. Documentation and API contract files are materially out of sync with implementation
- Impact: reviewer confusion, demo narrative inconsistency, integration mistakes.
- Evidence:
  - docs/API_CONTRACTS.md line 42 documents success wrapper format not used by actual endpoints.
  - docs/API_CONTRACTS.md line 238 references POST /ai/chat, while implemented route is /rag/chat.
  - README.md lines 155-156 still describe snapshot mismatch and direct fetch usage that are no longer true.

2. Database schema documentation includes entities not present in code
- Impact: architecture drift and misleading schema expectations.
- Evidence:
  - docs/DB_SCHEMA.md lines 99, 131, 174 define meetings, uploaded_documents, audit_logs tables.
  - backend/app/models/__init__.py exports no corresponding Meeting/uploaded_document/audit_log model.

3. Migration naming/versioning hygiene inconsistency
- Impact: maintainability and reviewer confidence risk.
- Evidence:
  - backend/app/db/migrations/versions/002_notifications.py uses revision id 005_add_notifications (line 14), which does not match filename numbering convention.

4. AI conversation history persistence is in-memory on backend
- Impact: cross-restart context loss; limited enterprise audit depth for assistant interactions.
- Evidence:
  - backend/app/services/ai_chat.py line 16 uses in-process _history_store dictionary.

## P2 Nice To Have

1. UI consistency polish pass
- Impact: minor visual inconsistency, not functional.
- Evidence:
  - frontend/src/pages/CreateEmployeePage.tsx line 298 uses custom-styled cancel button instead of shared button variant.
  - frontend/src/pages/NotificationsPage.tsx lines 34-39 uses emoji icons while most updated surfaces use Lucide icons.

2. Notification realtime architecture completion
- Impact: currently acceptable via polling, but real-time story is incomplete.
- Evidence:
  - frontend/src/hooks/index.ts lines 349 and 354 attempt websocket when VITE_WS_URL is set.
  - README.md lines 133 and 154 state backend websocket notifications endpoint is not implemented.

---

## Broken Features Summary

- Potential duplicate workflow creation during employee onboarding.
- Employee portal likely breaks or degrades for non-admin user personas.
- Pause/resume lifecycle actions do not produce a persisted workflow status distinction.

---

## Incomplete Workflows

- Calendar workflow stage exists as task/checklist semantics only; no actual scheduling subsystem.
- IT provisioning remains orchestration-task driven without integration execution.

---

## Demo Blockers

1. Duplicate workflow behavior in create employee flow.
2. Employee portal role mismatch and invalid query behavior.
3. Missing true calendar integration if reviewer tests scope item literally.
4. Broad audit visibility risk if role-based data access is part of rubric.

---

## Architecture Concerns

- Security boundary for audit logs is too permissive.
- Documentation and schema references drift from implementation.
- Migration naming conventions are inconsistent and may confuse release process.

---

## Component Review Verdict

Frontend: Good, with role/portal and minor consistency issues.
Backend: Good, with lifecycle-state persistence and authorization concerns.
Database: Operational for implemented entities; documentation overstates schema.
Workflow orchestration: Strong core implementation.
AI assistant: Strong MVP implementation; session persistence depth is limited.
Analytics: Strong and improved with enterprise KPIs.
Audit logs: Functionally present; authorization and provenance depth need tightening.
Employee portal: Good concept, currently blocked by role/data assumptions.
Documentation: Needs immediate alignment to current code for submission readiness.

---

## Final Submission Recommendation

Proceed only after resolving P0 items.

If timeline is limited, prioritize in this order:
1) duplicate workflow creation
2) employee portal access/data flow fixes
3) persisted lifecycle state semantics for pause/resume
4) audit endpoint authorization tightening
5) clear statement and scope note for calendar integration limitations

# AUDIT_LOG_RBAC_FIX

Date: 2026-06-07
Scope: Role-based authorization for audit log visibility

## Problem

`GET /api/v1/audit/logs` previously allowed all authenticated users to view the same cross-entity, global audit stream.

Risk:
- Overexposure of employee and workflow operational data.
- No separation by organizational role.

## Required Role Model

Implemented visibility model:

1. HR Admin
- Full audit access across all entities.

2. IT Admin
- Operational audit access only.
- Includes workflow/task/notification operational events.
- Excludes broad employee profile creation visibility.

3. Manager
- Limited audit visibility scoped to managed employees.
- Includes records tied to employees where `employees.manager_id == current_user.id`.

4. Employee
- Own activity only.
- Includes entries tied to own employee profile/workflow/task and own user-targeted notifications.

## Backend Changes

### 1) Endpoint now passes viewer identity to service
File: backend/app/api/v1/endpoints/audit.py

`list_logs` now receives:
- `viewer_user_id`
- `viewer_email`
- `viewer_role`

### 2) RBAC filtering implemented in audit service
File: backend/app/services/audit.py

Enhancements:
- Added role-aware filtering pipeline.
- Added viewer context resolution:
  - current employee id by email
  - managed employee ids for manager role
- Added entity relationship maps:
  - workflow -> employee
  - task -> workflow
- Added internal metadata tagging for entries (actor/user/employee/workflow linkage).
- Added role-specific filters:
  - full access for `hr_admin` and `admin`
  - operational-only action/entity set for `it_admin`
  - managed scope for `manager`
  - own scope for `employee`
- Sanitizes response output back to public schema fields only.

## Behavior Summary

- Unauthorized global audit visibility removed.
- Visibility now aligns to role and ownership scope.
- Existing audit response contract preserved (`items`, `total`; item fields unchanged).

## Validation

Added tests:
- backend/tests/unit/test_audit_rbac.py
  - `test_hr_admin_has_full_audit_access`
  - `test_it_admin_gets_operational_audit_access_only`
  - `test_manager_gets_limited_visibility_for_managed_scope`
  - `test_employee_sees_only_own_activity`

Regression check:
- Existing onboarding workflow test suite remains green.

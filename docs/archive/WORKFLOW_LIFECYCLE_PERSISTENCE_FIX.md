# WORKFLOW LIFECYCLE PERSISTENCE FIX

Date: 2026-06-07
Scope: Pause/Resume workflow lifecycle persistence and downstream consistency

## Problem Summary

Pause and Resume lifecycle actions were creating orchestration events, but did not reliably persist lifecycle state transitions on the workflow entity.

Impact:
- Workflow state could appear unchanged after refresh.
- Analytics could drift because counts are derived from persisted workflow state and employee onboarding status.
- Timeline had event history but state and status were not fully aligned.

## Root Cause

In onboarding lifecycle action handling:
- Pause did not update workflow.current_state.
- Resume did not restore a persisted state transition.
- Employee onboarding_status was not synchronized for pause/resume.

Result:
- Event timeline existed, but durable workflow and employee state did not fully reflect lifecycle actions.

## Requirements Addressed

Paused Workflow now includes:
1. persisted state
2. timeline update
3. analytics update
4. notification generation

Resumed Workflow now includes:
1. persisted state
2. timeline update
3. analytics update
4. notification generation

## Implementation Details

### 1) Persisted workflow lifecycle state
File: backend/app/services/onboarding.py

Changes:
- Added state mutation for pause:
  - workflow.current_state = "paused"
  - workflow.completed_at = None
- Added state mutation for resume:
  - If currently paused, resolve and restore the last pre-pause state.
  - Resume target is recovered from most recent workflow_paused event payload/state_from.

### 2) Persisted employee status (analytics source)
File: backend/app/services/onboarding.py

Changes:
- Pause sets employee.onboarding_status = "paused".
- Resume sets employee.onboarding_status:
  - "completed" if resumed state is completed
  - otherwise "in_progress"

This aligns dashboard employee status aggregations with lifecycle actions.

### 3) Timeline updates (orchestration event log)
File: backend/app/services/onboarding.py

Changes:
- Pause emits event_type workflow_paused with state_from and state_to=paused.
- Resume emits event_type workflow_resumed with state_from=paused and state_to=restored state.
- Event payload now stores both previous_state and current_state for traceability and replay support.

### 4) Notification generation
File: backend/app/services/onboarding.py

Changes:
- Existing workflow event notification pipeline is preserved and now receives corrected state_to values.
- Pause and Resume notifications are generated from mapped workflow events.

### 5) Refresh durability
Because workflow and employee states are now committed to the database during lifecycle actions, refreshed pages read the correct pause/resume status from APIs.

## Validation Coverage

Added tests in backend/tests/unit/test_onboarding_workflow.py:
- test_workflow_pause_persists_state_timeline_analytics_and_notification
- test_workflow_resume_restores_state_timeline_analytics_and_notification

Each test verifies:
- persisted workflow state
- persisted employee status
- lifecycle timeline event correctness
- notification creation
- analytics-facing aggregate updates

## Files Modified

- backend/app/services/onboarding.py
- backend/tests/unit/test_onboarding_workflow.py
- WORKFLOW_LIFECYCLE_PERSISTENCE_FIX.md

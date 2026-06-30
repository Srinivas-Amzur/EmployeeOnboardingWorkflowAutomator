# UI/UX Recommendations - Employee Onboarding Workflow Automator

Date: June 3, 2026
Scope: Recommendations only for missing UI/UX capabilities not already implemented.

Priority scale:
- P0 = Required for capstone completion
- P1 = Strongly recommended
- P2 = Nice to have

## Current UI Strengths (Already Implemented)
- Clean multi-page React UI with shared layout and reusable components.
- Dashboard, workflows, detail, notifications, analytics, assistant, and profile screens are implemented.
- Loading skeletons, empty states, and toast feedback exist across many flows.
- Responsive navigation and mobile menu are present.

## P0 Recommendations

## 1) Fix orchestration snapshot contract mismatch
Issue:
- Frontend expects `/onboarding/workflows/{id}/snapshot` while backend serves `/onboarding/workflows/{id}/orchestration`.

UX impact:
- Workflow preview state information can fail at runtime.

Recommendation:
- Align client endpoint to backend route and standardize naming in UI labels.

Acceptance criteria:
- Workflow preview loads snapshot state consistently.
- No network 404 for snapshot/orchestration calls during demo.

## 2) Role-aware UI access and affordances
Issue:
- UI shows most navigation/actions to all authenticated users, relying on backend rejection.

UX impact:
- Users can enter pages they cannot effectively use, causing confusing failures.

Recommendation:
- Add role-aware route guard and conditional action visibility for create/update/admin-only actions.

Acceptance criteria:
- Admin-only actions are hidden/disabled for non-admin roles.
- Navigation reflects user role.

## 3) Add explicit lifecycle action controls in workflow detail
Issue:
- Workflow lifecycle controls are limited to task status changes and generic workflow update.

UX impact:
- Operators cannot clearly execute pause/resume/cancel/reopen from UI.

Recommendation:
- Add lifecycle action panel with confirmation dialogs and reason capture.

Acceptance criteria:
- Lifecycle action buttons visible in workflow detail.
- Action history visible after each lifecycle command.

## P1 Recommendations

## 4) Unified error and recovery UX
Issue:
- Error handling consistency varies by page.

Recommendation:
- Standardize page-level error container with retry action and context-specific resolution hints.

Acceptance criteria:
- All top-level pages use a shared error pattern.
- Users can retry failed data loads without full refresh.

## 5) Workflow operations control center
Issue:
- Workflow detail is task-centric but lacks operational controls for escalations and ownership transfer.

Recommendation:
- Add operations sidebar:
  - assign/reassign owner,
  - add escalation note,
  - set target completion date,
  - view overdue/blocked quick actions.

Acceptance criteria:
- Operators can manage workflow operations without leaving detail page.

## 6) Employee self-service workspace
Issue:
- No dedicated employee-facing experience beyond profile page.

Recommendation:
- Add My Onboarding page with:
  - personal checklist,
  - due dates,
  - completion acknowledgments,
  - personal timeline.

Acceptance criteria:
- Employee role lands on self-service page by default.

## 7) Notification center usability upgrades
Issue:
- Notifications support list/read/unread; advanced filtering and preferences are absent.

Recommendation:
- Add filter chips (type/severity/date), search, and channel preference controls.

Acceptance criteria:
- Users can quickly isolate escalations or AI indexing updates.
- Preferences persist per user.

## 8) AI assistant UX improvements for trust
Issue:
- Assistant already shows citations but lacks confidence and memory controls.

Recommendation:
- Add:
  - source confidence badges,
  - per-session clear/reset controls,
  - response feedback actions.

Acceptance criteria:
- Users can rate responses and reset conversation context.

## P2 Recommendations

## 9) KPI storytelling layer in analytics
Recommendation:
- Add trend cards with directional deltas and explanatory tooltips (for non-technical stakeholders).

## 10) Accessibility polish
Recommendation:
- Add keyboard navigation audits, focus-ring consistency checks, and aria-label coverage review.

## 11) Demo mode UI
Recommendation:
- Add a toggleable demo banner and scenario presets to guide capstone narration.

## Suggested Implementation Sequence
1. P0 contract and role-aware UI fixes.
2. Lifecycle control panel and consistent error UX.
3. Self-service and notification preference enhancements.
4. AI trust and analytics storytelling improvements.

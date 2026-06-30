# UI Redesign Plan

## Objective
Modernize the Employee Onboarding Platform UI into an enterprise operations console inspired by Evoke Operations Portal, ServiceNow, Datadog, Jira, Rippling, Workday, and AWS Console.

## Non-Negotiable Guardrails
- UI/UX only.
- No backend API changes.
- No schema changes.
- No auth, Google Login, RBAC, workflow engine, AI assistant logic, notifications logic, analytics calculations, or export logic changes.

## Core Design System Targets
- Sidebar:
	- Background `#0B1220`
	- Hover `#172033`
	- Active `#2563EB`
	- Text `#E2E8F0`
	- Icons `#94A3B8`
	- Fixed width `280px`, collapsible
- Application background:
	- `#F8FAFC` or subtle enterprise gradient `linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%)`
- Card system:
	- Background `#FFFFFF`
	- Border `1px solid #E5E7EB`
	- Radius `12px`
	- Shadow `0 1px 2px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.04)`
	- Padding `24px`
- Typography:
	- Font family `Inter`
	- Page title `32px / 700`
	- Section title `18px / 600`
	- Label `12px / uppercase / 0.08em`
	- Body `14px`

## Sidebar Information Architecture
### OPERATIONS
- Dashboard
- Workflows
- Employees
- Calendar

### COLLABORATION
- Notifications
- AI Assistant

### ANALYTICS
- Analytics
- Audit Logs
- Reports

### ADMINISTRATION
- Profile
- Settings

## Page-by-Page Implementation
1. Shared shell and design tokens
- Apply global typography/color/card/background system.
- Implement fixed, collapsible enterprise sidebar with required sections.

2. Dashboard modernization
- Executive KPI row with: Total Employees, Active Workflows, Pending Tasks, Delayed Workflows, Completion Rate, Meetings Scheduled.
- Increase chart visual size by ~25%.
- Reduce whitespace and strengthen hierarchy.

3. Workflows list modernization
- Enterprise table columns: Workflow ID, Employee, Department, Current Stage, Progress, Status, Tasks, Created Date, Actions.
- Add search, filters, sorting, pagination.

4. My Portal modernization
- Self-service progress tracker, task completion cards, upcoming meetings, assigned documents, notifications summary.
- Timeline-style activity presentation.

5. Notifications activity center
- Category filters, severity colors, timeline, unread indicators.

6. AI Assistant workspace modernization
- Left: documents, upload, conversation history.
- Right: chat, suggested questions, sources panel/citations.

7. Analytics executive view
- KPI widgets, trend charts, completion metrics, department analytics, workflow bottleneck visibility.

## Validation Plan
1. Build frontend after each major batch.
2. Smoke test navigation/routes and key actions.
3. Verify no behavior changes in auth/RBAC/workflows/assistant/notifications/exports.
4. Confirm responsive behavior on desktop/laptop/tablet breakpoints.

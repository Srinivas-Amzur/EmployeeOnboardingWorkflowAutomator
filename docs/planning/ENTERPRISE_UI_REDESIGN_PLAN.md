# Enterprise UI Redesign Plan

## Objective
Refactor the frontend into a dense, enterprise operations dashboard experience inspired by ServiceNow, Rippling, Jira, Datadog, Salesforce, and Evoke dashboards, while preserving all existing application behavior.

## Hard Boundaries
- Do not modify backend code, APIs, auth logic, RBAC rules, workflow engine, database models, or AI orchestration behavior.
- UI/UX refactor only in frontend.

## Design Direction
- Layout pattern: collapsible left sidebar + persistent operations topbar + dense content canvas.
- Visual language: modern SaaS, data-forward, low-noise cards, compact table rows, operational status badges.
- Dark mode parity: all new components must support light and dark theme classes.
- Interaction model: keyboard accessible controls, clear active states, predictable navigation hierarchy.

## Incremental Rollout (Page by Page)
1. Foundation Shell (global)
- Replace top navigation with collapsible left sidebar.
- Add enterprise topbar (notifications, user context, quick actions, theme).
- Tighten global spacing scale to reduce whitespace and increase information density.

2. Operations Dashboard (`/dashboard`)
- Keep KPI strip and convert to executive widget language (status, throughput, risk).
- Preserve existing charts, increase readability and compactness.
- Keep recent workflows as dense enterprise table.

3. Workflows (`/onboarding`)
- Keep table-first workflow list.
- Improve filter toolbar density and table scannability.
- Preserve detail drawer behavior and workflow links.

4. Analytics (`/analytics`)
- Improve chart framing, axis legibility, and summary callouts.
- Keep report export controls and all existing actions.

5. Notifications (`/notifications`)
- Evolve into enterprise timeline with severity signaling and category filtering.
- Improve date grouping, timeline readability, and unread workflows.

6. AI Assistant (`/assistant`)
- Refactor into a professional analyst workspace (knowledge pane + chat canvas + citation review).
- Preserve upload/delete docs, RAG chat, and source citations.

7. Remaining pages (Profile, Employee Portal, Create Employee, Audit Logs, Details)
- Apply shell consistency, compact spacing, table/data-density standards.
- Preserve route behavior and form workflows.

## Acceptance Criteria Mapping
1. Collapsible left sidebar replaces top nav: foundation shell.
2. Professional enterprise dashboard: dashboard + analytics updates.
3. Higher information density: compact spacing/tables/widget sizing.
4. ~40% whitespace reduction: global spacing scale + page-specific compaction.
5. Responsive grid layouts: all major dashboard sections use adaptive grids.
6. Workflow cards to enterprise tables: workflows and dashboard recent items.
7. Executive KPI widgets: dashboard and analytics KPI strips.
8. Improved analytics visualizations: chart readability/layout updates.
9. Improved notification timeline: grouped timeline with severity and filters.
10. Improved AI Assistant workspace: split-pane ops assistant layout.
11. Tailwind + ShadCN-style SaaS components: utility-driven design with componentized primitives.
12. Existing functionality retained: route/action parity required.
13. Dark mode support: full parity for all new UI elements.
14. Production-quality UX: accessible controls, responsive layouts, robust empty/loading states.

## Validation
- Run frontend type-check/build after each increment.
- Manual smoke checks for nav, logout, notifications, assistant, and workflow detail navigation.

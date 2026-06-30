# Product UI Redesign Plan

## Objective
Transform the application from an internal admin portal feel into a commercial SaaS product matching the quality bar of Rippling, Deel, Linear, Notion, Jira, and GitHub Enterprise. No backend, API, auth, RBAC, database, workflow, AI, or notification logic is changed — only presentation layer.

---

## Current Issues

| Area | Issue |
|------|-------|
| Whitespace | Excessive padding (`p-6`, `space-y-8`) makes every page feel sparse |
| Typography | Low-contrast headers, inconsistent sizing, generic Tailwind defaults |
| Dashboard | Row of summary cards only — not a true command center |
| Workflow list | Card grid layout — lacks the scan speed of a data table |
| AI Assistant | Chat bubbles feel amateurish; no premium ChatGPT-like composition bar |
| Notifications | Flat list — missing visual timeline / severity distinction |
| KPI cards | Thin font, no trend spark or secondary metric |
| Viewport width | Max ~96rem with padded containers — not using 85-90% of viewport |
| Card height | Oversized padding inflates every card by 40-50% |
| Motion | Framer Motion imported but barely used beyond page fade |
| Responsive | Most pages collapse directly to mobile without a useful tablet breakpoint |

---

## Design System Changes

### Spacing scale reduction
- Replace `p-6` → `p-4` and `space-y-8` → `space-y-4` as the default shell
- Replace `rounded-3xl` → `rounded-2xl` for cards; `rounded-2xl` → `rounded-xl` for inputs
- Tight row height for table rows: `py-2.5` instead of `py-4`

### Typography upgrades
- Page titles: `text-2xl font-bold tracking-tight` (up from `text-xl`)
- Section headers: `text-xs font-semibold uppercase tracking-widest text-slate-500`
- Table headers: `text-[11px] font-bold uppercase tracking-wider text-slate-400`
- Metric values: `text-3xl font-bold tabular-nums`

### Viewport
- Layout container: `w-[min(90vw,100rem)]` — 90% desktop, 100% mobile
- Remove extra `px-4 sm:px-6 lg:px-8` padding inside layout

### Color / surface tokens
- Slightly more opaque backgrounds: `bg-white/96` light, `bg-slate-900/92` dark
- Add `--border-subtle` for inner table dividers: `rgba(148,163,184,0.14)`
- Active nav item: sharper contrast `bg-slate-950 text-white dark:bg-sky-500`

### Motion
- Row hover: `hover:bg-slate-50/80 dark:hover:bg-slate-800/60 transition-colors duration-100`
- Card hover: `hover:-translate-y-px hover:shadow-md transition-all duration-150`
- Page enter: already exists via framer-motion, keep

---

## Page-by-Page Changes

### 1. `index.css` — Global Tokens
- Tighten `.section-shell` padding to `p-3 sm:p-4`
- Add `.data-table` utility: zebra rows, sticky header, compact cells
- Add `.kpi-card` utility: fixed-height, strong metric font
- Add `.timeline-dot` for notification thread dots

### 2. `Layout.tsx`
- Update container to `w-[min(90vw,100rem)]`
- Reduce vertical `py` to `py-4 sm:py-5`

### 3. `Navbar.tsx` — Already regrouped in previous pass, keep

### 4. `DashboardPage.tsx` — Executive Command Center
**Before:** Row of 4 stat cards + charts below  
**After:**
- Top header bar with date, live metric strip (7 KPIs in single compact row)
- Left column: workflow state ring chart + activity feed
- Right column: task health bar + quick actions
- Compact cards, no wasted vertical space
- Lifecycle progress bar as thin horizontal stripe

### 5. `OnboardingListPage.tsx` — Enterprise Data Table
**Before:** Card grid with filter sidebar  
**After:**
- Filter bar (search + state + dept dropdowns) in single compact row
- Full-width sticky-header data table with sortable columns:
  `Employee | Department | State | Progress | Days | Tasks | Started | Actions`
- Status badge in-cell, progress mini-bar in-cell
- Row click opens right-side detail drawer (preserve existing logic)
- Pagination bar flush to table bottom

### 6. `AIAssistantPage.tsx` — ChatGPT Enterprise
**Before:** Two-panel with document list on left, chat on right  
**After:**
- Full-height chat pane (stretches to viewport)
- Slim collapsible sidebar for documents (icon rail collapsed by default on desktop)
- Premium composer: rounded textarea with send button + doc-count badge + model label
- Message bubbles: user right-aligned flat dark, assistant left-aligned with subtle border
- Source citations as expandable inline chips below each answer
- Suggested prompts as compact pill chips above composer (disappear after first message)

### 7. `NotificationsPage.tsx` — Timeline View
**Before:** Flat list grouped by date with filter row  
**After:**
- Sidebar filter: All / Workflow / AI / System (vertical pills)
- Main area: vertical timeline with date dividers as sticky labels
- Each entry: colored left border (severity), icon, title + description, relative timestamp
- Unread entries have a faint left glow; read entries desaturated
- Bulk "mark all read" button in sticky top bar

### 8. `AnalyticsDashboard.tsx` — Executive Report View
**Before:** Charts stacked vertically with export buttons  
**After:**
- KPI stat row (7 metrics) with trend delta badges
- 2-col chart grid: state ring + task bar side by side
- Data table below charts showing per-department breakdowns
- Export panel as floating action strip at top-right

### 9. `EmployeePortalPage.tsx` — Self-Service Hub
**Before:** Sections stacked with lots of vertical gap  
**After:**
- Compact profile hero (avatar + name + role + progress) in one line
- 3-col grid: tasks column, notifications column, docs/meetings column
- Progress steps as horizontal pill bar
- No empty-state padding inflation

### 10. Shared Primitives
- `Card.tsx`: reduce default padding, add hover lift
- `StatusBadge.tsx`: use `text-[11px]` font, tighter `px-1.5 py-0.5`
- `ProgressBar.tsx`: slimmer 4px track
- `Button.tsx`: tighter `py-1.5 px-3` for secondary actions

---

## Delivery Order

| Step | File(s) | Priority |
|------|---------|----------|
| 1 | `index.css` + `Layout.tsx` | High — affects every page |
| 2 | Shared primitives | High — cascades everywhere |
| 3 | `DashboardPage.tsx` | High — first thing users see |
| 4 | `OnboardingListPage.tsx` | High — core workflow UX |
| 5 | `AIAssistantPage.tsx` | High — key differentiator |
| 6 | `NotificationsPage.tsx` | Medium |
| 7 | `AnalyticsDashboard.tsx` | Medium |
| 8 | `EmployeePortalPage.tsx` | Medium |
| 9 | `OnboardingDetailPage.tsx` | Low — already decent |
| 10 | Build validation | Required |

---

## Constraints
- No backend / API / auth / RBAC / DB / workflow / AI / RAG / notification logic changes
- All existing hooks and data contracts preserved
- TypeScript and ESLint clean build required after each batch

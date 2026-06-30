# UI/UX Improvement Plan

## 1. Current UI Issues

- The app already has broad feature coverage, but the presentation is still mostly flat cards, standard spacing, and repeated page-local styling.
- Shared primitives such as `Card`, `Button`, `EmptyState`, `StatusBadge`, and `ProgressBar` are functional but visually conservative, which makes every page feel slightly different instead of part of one enterprise system.
- Page headers, filters, timelines, and data cards are useful, but hierarchy is inconsistent and the executive-level signals are not strong enough.
- Dark mode exists, but several page-local surfaces and controls rely on ad hoc color choices that can drift in contrast and polish.
- Loading, empty, and error states are present, but they are minimal and not yet aligned with a premium SaaS aesthetic.

## 2. Recommended Improvements

- Establish a stronger global design system with consistent spacing, radius, shadows, border treatments, and typography scale.
- Upgrade shared primitives first so all screens inherit the same visual language.
- Rework the shell navigation for better active states, user actions, theme toggle placement, and notification visibility.
- Recompose each major page into clearer information hierarchy with executive-friendly KPI blocks, supporting detail cards, and denser but cleaner data presentation.
- Improve accessibility across controls, focus states, empty states, and semantic structure.
- Normalize dark mode styles so all key surfaces, inputs, badges, and charts remain readable and consistent.

## 3. Screens Impacted

- Global shell and navigation
- Dashboard
- Onboarding workflows list
- Onboarding workflow detail
- Create employee form
- Notifications center
- Analytics dashboard
- AI assistant
- Profile page

## 4. Estimated Effort

- Global shell and shared components: medium
- Dashboard redesign: medium to large
- Workflow list and detail refresh: medium to large
- Employee creation UX: medium
- Notifications, analytics, assistant, and profile refreshes: medium each
- Accessibility and dark mode normalization: medium

## 5. Expected Visual Impact

- The application should feel substantially more like a modern enterprise SaaS product such as Linear, Jira, Rippling, or BambooHR.
- Executive-facing pages will read more clearly with better hierarchy, stronger KPI presentation, and improved spacing.
- The app should feel more polished on desktop and mobile, with better contrast, cleaner interactive states, and more intentional surface treatments.

## Delivery Order

1. Update shared shell, cards, buttons, empty states, badges, and loading states.
2. Refresh the dashboard and workflow pages.
3. Improve create employee, notifications, analytics, AI assistant, and profile pages.
4. Run frontend build validation after each page-level update batch.
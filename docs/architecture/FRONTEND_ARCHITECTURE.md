# Frontend Architecture

# Frontend Stack

- React 18+
- TypeScript
- Tailwind CSS
- TanStack Query
- Zustand

---

# Application Structure

frontend/src/

- components/
- pages/
- hooks/
- lib/
- types/

---

# Core Pages

- Login
- Dashboard
- Employees
- Workflows
- Tasks
- Notifications
- AI Assistant
- Analytics

---

# State Management

Server State:
TanStack Query

Global State:
Zustand

---

# UI Components

Reusable Components:
- onboarding cards
- task tables
- notification panels
- workflow timelines

---

# Styling Rules

Use:
- Tailwind utility classes
- responsive layouts
- dark mode support

Avoid:
- inline styles
- large monolithic components

---

# API Layer

All API calls:
frontend/src/lib/api.ts

Never:
- call fetch directly in components

---

# Security

- JWT cookies only
- no localStorage auth
- protected route wrappers
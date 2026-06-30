# 10-Minute Capstone Demo Script

## Demo Objective
Present the Employee Onboarding Workflow Automator as an implemented enterprise MVP, covering:
- problem statement,
- architecture,
- application walkthrough,
- AI features,
- workflow orchestration,
- analytics,
- technical implementation,
- future enhancements.

---

## 0:00 - 1:00 | Problem Statement
"In enterprise HR operations, onboarding is often fragmented across emails, sheets, and manual follow-ups. That causes missed tasks, delayed provisioning, weak visibility, and poor accountability.

This project solves that by centralizing onboarding into a workflow-driven platform with orchestration, notifications, analytics, and an AI assistant grounded in policy documents."

## 1:00 - 2:00 | Architecture Overview
"The system is split into a React TypeScript frontend and a FastAPI backend.

On the backend, business logic sits in services over SQLAlchemy models and Pydantic schemas. For AI, LangGraph orchestrates onboarding lifecycle transitions, and LangChain plus ChromaDB power retrieval-grounded assistant responses. PostgreSQL stores transactional onboarding data."

Action:
1. Open architecture diagram in `docs/architecture.mmd`.
2. Point out major flow: Users -> Frontend -> API -> Services -> Orchestration/Notifications/RAG -> PostgreSQL + ChromaDB.

## 2:00 - 4:00 | Application Walkthrough
"I'll walk through the primary HR flow end-to-end."

Action:
1. Login with admin/HR account.
2. Show dashboard KPIs and charts.
3. Navigate to **Create Employee**.
4. Create a sample employee (e.g., John Doe) and submit.

Narration:
- "The system generates a company email: john.doe@company.local — no external provider needed."
- "A welcome email with all employee details is sent to the employee, manager, and HR."
- "Employee creation triggers orchestration bootstrap in the service layer."
- "The company email is displayed in workflow detail, employee portal, and onboarding list."

## 4:00 - 5:30 | Workflow Orchestration & Milestone Emails
Action:
1. Open **Onboarding Workflows**.
2. Open the newly created workflow.
3. Show the Employee card with company email.
4. Show timeline/state and generated tasks.
5. Mark tasks as completed and observe state progression.

Narration:
- "Task updates trigger orchestration sync."
- "Workflow state and completion percentage are recalculated."
- "When the workflow enters a milestone state, emails are sent to employee, manager, and HR."
- "Milestones: Onboarding Started, HR Review Completed, IT Provisioning Completed, Documents Shared, Onboarding Completed."
- "Events are persisted for auditability."
Action:
1. Open **Onboarding Workflows**.
2. Open the newly created workflow.
3. Show timeline/state and generated tasks.
4. Mark 1-2 tasks as completed.

Narration:
- "Task updates trigger orchestration sync." 
- "Workflow state and completion percentage are recalculated." 
- "Events are persisted for auditability." 

## 5:30 - 6:30 | Notification Flow
Action:
1. Open **Notifications**.
2. Show unread count and new event entries.
3. Mark one notification read, then mark all read.

Narration:
- "Notifications are generated from workflow events, task transitions, and AI indexing outcomes."
- "Current production behavior uses polling; backend WebSocket endpoint is future scope."

## 6:30 - 7:30 | Analytics Flow
Action:
1. Open **Analytics** page.
2. Highlight workflow distribution, task distribution, and completion trend.

Narration:
- "These aggregates are computed from workflow, task, and employee data in the analytics service."
- "This gives operations leaders immediate visibility into onboarding health."

## 7:30 - 9:00 | AI Assistant + RAG
Action:
1. Open **AI Assistant**.
2. Show indexed docs list.
3. Upload a policy PDF if needed.
4. Ask a policy question.
5. Show grounded response with citations.

Narration:
- "Upload flow validates and chunks PDFs, embeds them, and stores vectors in per-user Chroma collections."
- "Chat answers are grounded by retrieved chunks and produced through an LCEL chain."

## 9:00 - 10:00 | Technical Summary + Future Enhancements
"Technically, this MVP demonstrates:
- layered API/service architecture,
- JWT cookie authentication,
- LangGraph-driven workflow orchestration,
- event audit persistence,
- integrated notification center,
- analytics aggregation,
- retrieval-grounded AI assistant.

Future enhancements:
- backend WebSocket notification endpoint,
- production email provider integration,
- calendar sync integrations,
- alignment of frontend workflow snapshot path with backend orchestration endpoint."

Close:
"The platform is implemented and operational for core onboarding automation, while remaining gaps are clearly identified as next-phase scope."

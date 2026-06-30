# PROMPT_SEQUENCES

These are reconstructed Copilot Agent Mode prompt sequences that align with the implemented codebase.

## 1) Authentication
1. "Create FastAPI auth endpoints for register/login/logout/me/change-password using JWT in httpOnly cookies and role fields in token payload."
2. "Add password hashing and verification with bcrypt/passlib and pydantic password strength validators."
3. "Build React login page with protected routes and auth bootstrap that calls /auth/me on startup."
4. "Add change-password modal and keep session alive by rotating cookie token after password change."

## 2) Employee Management
1. "Implement Employee SQLAlchemy model and pydantic schemas for create/update/response."
2. "Add EmployeeService with create/get/list/update using async SQLAlchemy."
3. "Wire /employees endpoints with admin guard for create/list/update and authenticated read."
4. "Create frontend page for employee creation with form validation and optional auto-workflow creation."

## 3) Workflow Orchestration
1. "Implement onboarding workflow/task models and CRUD service methods."
2. "Build LangGraph orchestrator with states initiated, hr_review, provisioning, meetings_scheduled, documents_shared, completed."
3. "Generate deterministic task blueprints per stage and sync workflow state from task status."
4. "Persist orchestration events and provide workflow snapshot/events endpoints."

## 4) Notifications
1. "Create notifications model, migration, schemas, and service for create/list/unread/mark-read."
2. "Trigger notifications on task assignment, task completion, workflow state events, and AI indexing completion."
3. "Expose notification API endpoints and build frontend notification center with unread filtering and mark-all-read."
4. "Add navbar unread badge polling and dropdown preview."

## 5) RAG Assistant
1. "Implement PDF upload validation, text extraction, and chunking service for onboarding docs."
2. "Integrate ChromaDB with per-user collections and embeddings through LiteLLM-configured OpenAIEmbeddings."
3. "Create RAG endpoints for upload, search, chat, list documents, and delete document."
4. "Build AI assistant page with file upload, suggested prompts, chat, and source citation rendering."

## 6) Analytics Dashboard
1. "Implement analytics service to aggregate workflow counts by state, task counts by status, and employee counts."
2. "Expose /analytics/dashboard endpoint."
3. "Create dashboard and analytics pages using chart components and query hooks."
4. "Add loading states, empty states, and route-level lazy loading for page performance."

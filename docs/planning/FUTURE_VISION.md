# FUTURE_VISION

## Current MVP Scope (Delivered)
1. JWT cookie auth and role-gated APIs
2. Employee profile onboarding intake
3. Workflow/task lifecycle management
4. LangGraph-based deterministic orchestration and event log
5. In-app notifications (API + UI)
6. RAG assistant over uploaded PDF policy documents
7. Dashboard analytics from aggregate workflow/task/employee metrics
8. Docker Compose local deployment path

## Future Enhancements (Near-Term)
1. Fix API/UI contract mismatch for workflow snapshot endpoint naming.
2. Standardize frontend API usage (remove direct fetch usage from OnboardingDetail page).
3. Add backend websocket notification stream endpoint if true push updates are required.
4. Add richer workflow filters and bulk actions.
5. Add document metadata and pagination for larger RAG libraries.
6. Expand analytics with trend persistence and export.

## Stretch Goals
1. Calendar integrations for meeting scheduling.
2. Email delivery provider integration (SendGrid/SES/etc.)
3. SLA policies and automated reminder jobs.
4. Multi-turn assistant memory persistence beyond in-memory session store.
5. E2E UI automation and performance testing pipelines.

## Enterprise Expansion Vision
1. Identity and security
- SSO (OIDC/SAML), MFA, SCIM provisioning, stronger audit trails.

2. Platform scale
- Redis caching, async job queue, managed vector DB option, horizontal API scaling.

3. Governance and compliance
- Data retention policies, PII controls, admin audit exports, compliance reporting.

4. Multi-tenant operations
- Tenant-scoped isolation, policy templates, configurable onboarding playbooks.

5. Intelligence roadmap
- Predictive onboarding risk scoring, bottleneck analytics, policy gap detection.

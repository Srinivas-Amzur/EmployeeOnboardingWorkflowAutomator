# Employee Onboarding Workflow Automator - Production Gap Analysis

Date: June 3, 2026
Scope: Full-stack review of implemented backend, frontend, and documentation artifacts.

Priority scale:
- P0 = Required for capstone completion
- P1 = Strongly recommended
- P2 = Nice to have

## Executive Summary
The application is a strong MVP with core onboarding workflows, task management, orchestration events, notifications, analytics, and RAG assistant implemented.

Primary gaps are enterprise-hardening and demo-readiness gaps rather than missing core MVP functionality. The most critical items for capstone review are:
- role-specific UX/RBAC experience is not complete,
- workflow lifecycle controls are limited,
- one frontend/backend orchestration endpoint mismatch impacts observability,
- capstone demonstration tooling is not yet packaged.

## 1) Missing Enterprise Features
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P1 | SSO/SAML/OIDC integration not implemented | Enterprise identity integration is a common production requirement | Auth is JWT email/password based only in backend auth endpoints and security utilities |
| P1 | MFA and device/session management not implemented | Security baseline for production HR systems | No MFA challenge flow or session/device inventory endpoints |
| P1 | Email delivery is placeholder only | Enterprise communications are not production-deliverable | Notification service uses a placeholder email sender function |
| P2 | Multi-tenant isolation model not implemented | Needed for SaaS-scale tenancy boundaries | No org/tenant model or tenant-scoped RBAC in models/services |

## 2) Missing UI/UX Improvements
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P0 | Frontend workflow snapshot API path mismatch | Orchestration snapshot UX can fail and weaken demo reliability | Frontend calls `/onboarding/workflows/{id}/snapshot`, backend exposes `/onboarding/workflows/{id}/orchestration` |
| P1 | Role-aware navigation and action gating in UI is limited | Non-admin users can reach admin pages then fail at API layer, creating poor UX | Navbar exposes all major routes; route-level required role checks are mostly not used |
| P1 | Error handling UX is inconsistent across pages | Enterprise demos expect clear recoverable error states | Some pages have robust empty/error states, others log errors or show minimal messaging |
| P2 | No dedicated keyboard accessibility and focus-management review artifacts | Accessibility maturity expected in production assessments | No explicit a11y-focused components/tests in current UI implementation |

## 3) Missing RBAC Functionality
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P0 | RBAC is coarse-grained (`admin`/`hr_admin` vs authenticated user) | Capstone review often expects explicit permission matrix per action | `get_current_admin_user` checks only two roles; no granular permission model |
| P1 | No resource-level authorization checks (department/team ownership) | Prevents over-broad access in larger organizations | Workflow/task reads rely on authenticated access without scoped ownership logic |
| P1 | UI does not present role-specific feature sets | Demonstrating RBAC effectiveness requires visible role differentiation | Most protected pages are available to any authenticated user in routing |

## 4) Missing Workflow Lifecycle Actions
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P0 | No explicit lifecycle actions for pause/resume/cancel/reopen | Enterprise workflows require controlled lifecycle operations beyond task status updates | Onboarding endpoints implement create/get/list/update/progress/events/tasks but no dedicated lifecycle action endpoints |
| P1 | No approval/rejection transitions for HR or manager checkpoints | Missing governance handoffs in lifecycle control | State progression is derived by orchestration/task completion; no explicit approve/reject action API |
| P2 | No SLA deadline override/escalation management actions | Operations teams need manual intervention controls | Escalations are generated automatically; no escalation management endpoints |

## 5) Missing Auditability Features
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P1 | Audit trail is strong for orchestration events but weak for user-driven CRUD changes | Production audits require actor + before/after for manual changes | Orchestration events table exists; no generalized audit log for employee/task/workflow edits |
| P1 | No immutable audit export/report endpoint | Compliance and audit reviews often need exportable records | No API for downloadable audit reports or signed audit snapshots |
| P2 | No explicit correlation between API request IDs and persisted business events | Troubleshooting and incident forensics benefit from end-to-end traceability | Request IDs exist in middleware logs; not persisted with domain records |

## 6) Missing Employee Self-Service Features
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P1 | No employee-specific task inbox/my-onboarding page | Self-service onboarding experience is expected for end users | Current pages focus on global workflow views; profile page is account-only |
| P1 | No self-upload/acknowledgment for onboarding documents | Employee ownership and completion verification are reduced | RAG upload is available for assistant ingestion, not employee checklist acknowledgments |
| P2 | No personal onboarding milestone timeline with acknowledgment actions | Improves employee transparency and completion confidence | Timeline views exist at workflow level, not personalized self-service checkpoints |

## 7) Missing Dashboard KPIs
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P1 | No SLA metrics (overdue rate, average time-in-state, cycle time) | Enterprise operations evaluate timeliness, not only counts | Analytics endpoint returns aggregate counts and average completion only |
| P1 | No assignee/department workload KPIs | Helps staffing and bottleneck management | Existing analytics does not include assignee workload distribution |
| P2 | No trend comparison windows (week-over-week/month-over-month) | Leadership dashboards typically need trend deltas | Current charts show recent distribution/trend without comparative windows |

## 8) Missing Notifications Functionality
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P1 | No backend real-time push channel for notifications | Low-latency enterprise UX benefits from push over polling | Frontend has optional WS hook; backend has no WebSocket notifications endpoint |
| P1 | No notification preferences (channel/type/quiet hours) | Users need control over alert volume and channels | Notification APIs support list/read/unread-count only |
| P2 | No digest/snooze/bulk archive lifecycle | Helps prevent alert fatigue in long-running operations | No digest/snooze/archive notification API support |

## 9) Missing AI Assistant Enhancements
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P1 | Conversation memory is in-memory and not durable across restarts | Production assistants need persistent conversational continuity | AI chat service stores session history in process memory dictionary |
| P1 | No admin controls for AI policy guardrails/versioning | Enterprise requires controllable response behavior | Prompt and model config are centralized but no runtime admin policy management |
| P2 | No feedback loop (thumbs up/down, correction capture) | Continuous quality improvement is harder without feedback telemetry | Assistant UI supports ask/upload/citations but no response feedback capture |

## 10) Missing Capstone Demonstration Features
| Priority | Gap | Why it matters | Evidence in code |
|---|---|---|---|
| P0 | No one-command demo data seeding/reset flow | Capstone demos need deterministic repeatability | No dedicated seed/reset command documented in demo artifacts |
| P0 | No role-switch demo support package (admin vs employee persona) | RBAC walkthrough is harder without prebuilt personas and scripted data | Auth exists, but no curated role-based demo harness |
| P1 | No "demo health checklist" page or script validating all endpoints/pages before presentation | Reduces risk of live demo failures | Current docs include walkthrough scripts but no automated pre-demo validation bundle |

## Recommended Priority Backlog

## P0 (Capstone must-fix)
1. Align workflow snapshot frontend/backend API contract (`snapshot` vs `orchestration`).
2. Add explicit workflow lifecycle action endpoints and UI controls (pause/resume/cancel/reopen).
3. Deliver demonstrable RBAC experience in UI (role-aware navigation/action visibility).
4. Add deterministic demo seed/reset and role-based demo dataset scripts.

## P1 (Strongly recommended)
1. Introduce granular permission matrix (beyond binary admin guard).
2. Add persistent audit trail for user-driven CRUD with actor and before/after state.
3. Add backend real-time notification channel and user notification preferences.
4. Expand analytics with SLA and bottleneck KPIs.
5. Add durable AI conversation memory and basic assistant governance controls.
6. Add employee self-service onboarding workspace.

## P2 (Nice to have)
1. Multi-tenant model and tenant-scoped policy controls.
2. Notification digest/snooze/archive.
3. Comparative analytics windows and richer executive dashboards.
4. Assistant feedback telemetry and quality loop.

# Workflow States — Employee Onboarding Workflow Automator

# Overview

The onboarding workflow is managed using LangGraph orchestration.

The workflow engine coordinates:
- onboarding lifecycle
- state transitions
- task dependencies
- escalation handling
- notifications
- completion tracking

---

# Workflow Lifecycle

initiated
↓
hr_review
↓
provisioning
↓
meetings_scheduled
↓
documents_shared
↓
completed

---

# State Definitions

## initiated

Description:
Initial onboarding workflow created.

Actions:
- create onboarding workflow
- initialize onboarding tasks
- assign onboarding owner

Triggers:
- HR creates employee onboarding request

---

## hr_review

Description:
HR validates onboarding details.

Actions:
- validate employee information
- verify joining date
- assign manager
- approve onboarding process

---

## provisioning

Description:
IT provisioning workflow starts.

Tasks:
- email account creation
- Slack/MS Teams provisioning
- VPN access
- GitHub/Jira access
- hardware allocation

Dependencies:
- HR approval completed

---

## meetings_scheduled

Description:
Onboarding meetings scheduled.

Meetings:
- HR orientation
- manager introduction
- team onboarding
- compliance meetings

---

## documents_shared

Description:
Employee onboarding documents distributed.

Documents:
- handbook
- NDA
- policies
- compliance PDFs

RAG Pipeline:
- chunking
- embeddings
- ChromaDB indexing

---

## completed

Description:
Onboarding process successfully completed.

Completion Criteria:
- all tasks completed
- meetings attended
- required documents acknowledged

---

# Escalation Rules

## Delayed Provisioning
Trigger:
task overdue > 24 hours

Action:
notify HR + IT Admin

---

## Missing Documents
Trigger:
required docs not uploaded

Action:
notify employee

---

# Notification Triggers

| Event | Recipients |
|---|---|
| Workflow Started | Employee, HR |
| Provisioning Started | IT Admin |
| Meeting Scheduled | Employee, Manager |
| Documents Shared | Employee |
| Workflow Completed | HR, Employee |

---

# LangGraph Responsibilities

The orchestrator:
- validates state transitions
- checks task dependencies
- triggers notifications
- tracks workflow progress
- handles escalations
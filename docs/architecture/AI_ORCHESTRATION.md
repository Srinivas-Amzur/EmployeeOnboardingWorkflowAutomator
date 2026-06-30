# AI Orchestration Architecture

# Overview

The platform uses LangGraph for workflow orchestration.

The orchestrator coordinates:
- onboarding lifecycle
- task generation
- notifications
- escalations
- workflow transitions

---

# Workflow States

- initiated
- hr_review
- provisioning
- meetings_scheduled
- documents_shared
- completed

---

# LangGraph Nodes

## create_workflow
Initializes onboarding state.

## assign_tasks
Creates onboarding tasks.

## provisioning
Triggers IT provisioning flow.

## scheduling
Schedules onboarding meetings.

## document_distribution
Shares onboarding documents.

## notifications
Sends onboarding notifications.

## completion
Marks onboarding completed.

---

# AI Responsibilities

The AI system:
- coordinates onboarding flow
- monitors incomplete tasks
- summarizes onboarding progress
- explains onboarding procedures

---

# AI Models

Supported:
- gemini/gemini-2.5-flash
- gpt-4o

---

# LiteLLM Rules

ALL AI calls:
- use LiteLLM proxy
- include user metadata
- use LCEL syntax

---

# LCEL Pattern

Use:
prompt | llm | parser

Avoid:
- LLMChain
- SequentialChain
- ConversationalRetrievalChain
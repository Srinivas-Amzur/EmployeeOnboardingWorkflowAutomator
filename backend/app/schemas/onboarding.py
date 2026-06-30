"""
Onboarding workflow and task schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OnboardingTaskBase(BaseModel):
    """Base task schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    assigned_to: UUID | None = None
    status: str = Field(default="pending")
    priority: str = Field(default="medium")
    due_date: datetime | None = None


class OnboardingTaskCreate(OnboardingTaskBase):
    """Task creation schema."""

    workflow_id: UUID


class OnboardingTaskUpdate(BaseModel):
    """Task update schema."""

    title: str | None = None
    description: str | None = None
    assigned_to: UUID | None = None
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None


class OnboardingTaskResponse(OnboardingTaskBase):
    """Task response schema."""

    id: UUID
    workflow_id: UUID
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OnboardingWorkflowBase(BaseModel):
    """Base workflow schema."""

    employee_id: UUID
    current_state: str = Field(default="initiated")
    completion_percentage: int = Field(default=0, ge=0, le=100)


class OnboardingWorkflowCreate(OnboardingWorkflowBase):
    """Workflow creation schema."""

    pass


class OnboardingWorkflowUpdate(BaseModel):
    """Workflow update schema."""

    current_state: str | None = None
    completion_percentage: int | None = None


class OnboardingWorkflowResponse(OnboardingWorkflowBase):
    """Workflow response schema."""

    id: UUID
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowActionRequest(BaseModel):
    """Lifecycle action request for workflow controls."""

    action: str = Field(..., pattern="^(pause|resume|escalate|complete)$")
    note: str | None = Field(default=None, max_length=500)


class WorkflowActionResponse(BaseModel):
    """Result payload for workflow lifecycle action."""

    workflow_id: UUID
    action: str
    current_state: str
    completion_percentage: int
    message: str
    event_id: UUID
    performed_at: datetime


class OrchestrationEventResponse(BaseModel):
    """Persisted orchestration event response."""

    id: UUID
    workflow_id: UUID
    employee_id: UUID
    event_type: str
    status: str
    state_from: str | None
    state_to: str | None
    message: str
    payload: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrchestrationStateSnapshot(BaseModel):
    """Summary schema for workflow orchestration state."""

    workflow_id: UUID
    employee_id: UUID
    current_state: str
    completion_percentage: int
    total_tasks: int
    completed_tasks: int

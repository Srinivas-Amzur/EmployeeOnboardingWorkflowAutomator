"""Meeting schemas for onboarding calendar MVP."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MeetingBase(BaseModel):
    """Shared fields for meeting payloads."""

    employee_id: UUID
    workflow_id: UUID
    meeting_type: str = Field(..., pattern="^(orientation|manager_introduction|team_onboarding|custom)$")
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=1500)
    scheduled_for: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    location: str | None = Field(default=None, max_length=255)
    meeting_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="scheduled", pattern="^(scheduled|completed|cancelled)$")


class MeetingCreate(MeetingBase):
    """Payload to create a new onboarding meeting."""

    pass


class MeetingUpdate(BaseModel):
    """Payload to update an existing onboarding meeting."""

    meeting_type: str | None = Field(default=None, pattern="^(orientation|manager_introduction|team_onboarding|custom)$")
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=1500)
    scheduled_for: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    location: str | None = Field(default=None, max_length=255)
    meeting_url: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, pattern="^(scheduled|completed|cancelled)$")


class MeetingResponse(MeetingBase):
    """Meeting response model."""

    id: UUID
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleMeetingRequest(BaseModel):
    """Request payload used by convenience schedule endpoints."""

    scheduled_for: datetime | None = None
    duration_minutes: int = Field(default=60, ge=15, le=480)
    location: str | None = Field(default=None, max_length=255)
    meeting_url: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=500)


class ScheduleCoreMeetingsResponse(BaseModel):
    """Response for bulk meeting scheduling in onboarding workflows."""

    workflow_id: UUID
    employee_id: UUID
    created_count: int
    meetings: list[MeetingResponse]

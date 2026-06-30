"""Notification schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Supported notification event categories."""

    WORKFLOW_STARTED = "workflow_started"
    ONBOARDING_APPROVED = "onboarding_approved"
    PROVISIONING_STARTED = "provisioning_started"
    HR_REVIEW_COMPLETED = "hr_review_completed"
    IT_PROVISIONING_COMPLETED = "it_provisioning_completed"
    MEETINGS_SCHEDULED = "meetings_scheduled"
    DOCUMENTS_SHARED = "documents_shared"
    WORKFLOW_TRANSITION = "workflow_transition"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    ONBOARDING_COMPLETED = "onboarding_completed"
    AI_ORCHESTRATION = "ai_orchestration"
    AI_INDEXING_COMPLETED = "ai_indexing_completed"
    ESCALATION = "escalation"


class NotificationResponse(BaseModel):
    """Notification response payload."""

    id: UUID
    user_id: UUID
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool
    read_at: datetime | None
    payload: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Paginated notification list response."""

    items: list[NotificationResponse]
    unread_count: int = Field(ge=0)


class NotificationUnreadCountResponse(BaseModel):
    """Unread count response."""

    count: int = Field(ge=0)


class NotificationMarkAllReadResponse(BaseModel):
    """Bulk mark-read operation result."""

    updated: int = Field(ge=0)

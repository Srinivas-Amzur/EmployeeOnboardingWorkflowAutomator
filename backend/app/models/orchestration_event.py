"""
Persistence model for onboarding orchestration events.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin, UUIDMixin


class OnboardingOrchestrationEvent(Base, UUIDMixin, TimestampMixin):
    """Stores LangGraph orchestration events for auditability and debugging."""

    __tablename__ = "onboarding_orchestration_events"

    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("onboarding_workflows.id"), nullable=False, index=True)
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="success")
    state_from: Mapped[str | None] = mapped_column(String(50), nullable=True)
    state_to: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<OnboardingOrchestrationEvent(id={self.id}, workflow_id={self.workflow_id}, "
            f"event_type={self.event_type}, status={self.status})>"
        )
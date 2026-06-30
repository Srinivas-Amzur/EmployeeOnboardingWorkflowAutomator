"""Onboarding meeting model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin, UUIDMixin


class OnboardingMeeting(Base, UUIDMixin, TimestampMixin):
    """Meeting scheduled as part of onboarding workflow execution."""

    __tablename__ = "onboarding_meetings"

    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("onboarding_workflows.id"), nullable=False, index=True)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    meeting_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scheduled", index=True)

    def __repr__(self) -> str:
        return (
            f"<OnboardingMeeting(id={self.id}, employee_id={self.employee_id}, "
            f"workflow_id={self.workflow_id}, type={self.meeting_type}, status={self.status})>"
        )

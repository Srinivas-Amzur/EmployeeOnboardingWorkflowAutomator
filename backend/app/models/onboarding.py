"""
Onboarding workflow model.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin, UUIDMixin


class OnboardingWorkflow(Base, UUIDMixin, TimestampMixin):
    """Onboarding workflow tracking."""

    __tablename__ = "onboarding_workflows"

    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), nullable=False)
    current_state: Mapped[str] = mapped_column(String(50), nullable=False, default="initiated")
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<OnboardingWorkflow(id={self.id}, employee_id={self.employee_id}, state={self.current_state})>"

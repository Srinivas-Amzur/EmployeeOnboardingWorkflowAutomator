"""
Employee model.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin, UUIDMixin


class Employee(Base, UUIDMixin, TimestampMixin):
    """Employee model for onboarding."""

    __tablename__ = "employees"

    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    company_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=True)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    onboarding_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, email={self.email}, status={self.onboarding_status})>"

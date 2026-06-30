"""
Employee schemas for request/response validation.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class EmployeeBase(BaseModel):
    """Base employee schema."""

    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    department: str = Field(..., max_length=255)
    designation: str = Field(..., max_length=255)
    joining_date: date


class EmployeeCreate(EmployeeBase):
    """Employee creation schema."""

    manager_id: UUID | None = None


class EmployeeUpdate(BaseModel):
    """Employee update schema."""

    first_name: str | None = None
    last_name: str | None = None
    department: str | None = None
    designation: str | None = None
    manager_id: UUID | None = None
    onboarding_status: str | None = None


class EmployeeResponse(EmployeeBase):
    """Employee response schema."""

    id: UUID
    company_email: str | None = None
    manager_id: UUID | None
    onboarding_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

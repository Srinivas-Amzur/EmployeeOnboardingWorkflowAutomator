"""
User schemas for request/response validation.
"""

from datetime import datetime
import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


PASSWORD_UPPERCASE_RE = re.compile(r"[A-Z]")
PASSWORD_LOWERCASE_RE = re.compile(r"[a-z]")
PASSWORD_NUMBER_RE = re.compile(r"\d")
PASSWORD_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")


def validate_password_strength(password: str) -> str:
    """Validate password complexity and return the original password."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not PASSWORD_UPPERCASE_RE.search(password):
        raise ValueError("Password must include at least one uppercase letter")
    if not PASSWORD_LOWERCASE_RE.search(password):
        raise ValueError("Password must include at least one lowercase letter")
    if not PASSWORD_NUMBER_RE.search(password):
        raise ValueError("Password must include at least one number")
    if not PASSWORD_SPECIAL_RE.search(password):
        raise ValueError("Password must include at least one special character")
    return password


class UserBase(BaseModel):
    """Base user schema."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    role: str = Field(default="employee")


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(BaseModel):
    """User update schema."""

    name: str | None = Field(None, max_length=255)
    role: str | None = None


class UserResponse(UserBase):
    """User response schema."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    """Google Sign-In request schema."""

    id_token: str = Field(..., min_length=10)


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    token_type: str
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    """Request schema for password change."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def validate_confirm_password(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Confirm password must match new password")
        return self


class MessageResponse(BaseModel):
    """Generic structured response with a message."""

    message: str

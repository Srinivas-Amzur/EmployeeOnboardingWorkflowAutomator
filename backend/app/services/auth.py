"""
Authentication service for user lookup and password management.
"""

from uuid import UUID

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select

from ..core.config import get_settings
from ..core.security import hash_password, verify_password
from ..models import User
from ..schemas import ChangePasswordRequest, UserCreate
from .base import BaseService


class AuthService(BaseService):
    """Service for authentication-related persistence and validation."""

    def __init__(self, db):
        super().__init__(db)
        self.settings = get_settings()

    async def get_user_by_email(self, email: str) -> User | None:
        """Return a user by email if present."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_user_by_id(self, user_id: str | UUID) -> User | None:
        """Return a user by id if present."""
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except (ValueError, TypeError):
                return None
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        user = await self.get_user_by_email(email)
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(self, request: UserCreate) -> User:
        """Create a new user with a securely hashed password."""
        user = User(
            name=request.name,
            email=request.email,
            hashed_password=hash_password(request.password),
            role=request.role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_google_user(self, google_token: str) -> User:
        """Validate Google token and return an existing or newly created user."""
        if not self.settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google login is not configured",
            )

        try:
            payload = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                self.settings.GOOGLE_CLIENT_ID,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
            ) from exc

        email = payload.get("email")
        name = payload.get("name") or email
        google_sub = payload.get("sub")
        email_verified = payload.get("email_verified")

        if not email or not google_sub or not email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account is missing required verified identity fields",
            )

        user = await self.get_user_by_email(email)
        if user:
            if not user.google_id:
                user.google_id = google_sub
                await self.db.commit()
                await self.db.refresh(user)
            return user

        user = User(
            name=name,
            email=email,
            hashed_password=None,
            google_id=google_sub,
            role="employee",
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, request: ChangePasswordRequest) -> User:
        """Validate current password and replace it with a bcrypt hash."""
        if not verify_password(request.current_password, user.hashed_password or ""):
            raise ValueError("Current password is incorrect")
        if verify_password(request.new_password, user.hashed_password or ""):
            raise ValueError("New password must be different from the current password")

        user.hashed_password = hash_password(request.new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user
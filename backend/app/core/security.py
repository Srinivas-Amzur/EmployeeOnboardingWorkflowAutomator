"""
Security utilities for authentication and authorization.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from pydantic import BaseModel
from jose import JWTError, jwt

from .config import get_settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


class TokenData(BaseModel):
    """Token payload data."""

    sub: str  # user id
    email: str
    role: str
    exp: datetime


class Token(BaseModel):
    """Token response."""

    access_token: str
    token_type: str


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    # Invalid or empty hashes should fail authentication, not crash the request.
    if not hashed_password:
        return False

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(
    subject: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> Token:
    """
    Create a JWT access token.

    Args:
        subject: User ID
        email: User email
        role: User role
        expires_delta: Token expiration time delta

    Returns:
        Token object with access token and type
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + settings.ACCESS_TOKEN_EXPIRE_TIMEDELTA

    payload = {
        "sub": str(subject),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return Token(access_token=encoded_jwt, token_type="bearer")


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)

        if user_id is None or email is None:
            return None

        return TokenData(sub=user_id, email=email, role=role, exp=exp)
    except JWTError:
        return None

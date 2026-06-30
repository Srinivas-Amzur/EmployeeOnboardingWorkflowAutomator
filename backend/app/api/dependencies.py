"""
API dependencies for authentication, database access, etc.
"""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import decode_token, TokenData
from ..db.session import get_db

# Type aliases
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    access_token: Annotated[str | None, Cookie()] = None,
) -> TokenData:
    """
    Dependency to get current authenticated user.

    Args:
        access_token: JWT token from httpOnly cookie

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_data = decode_token(access_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return token_data


async def get_current_admin_user(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> TokenData:
    """
    Dependency to ensure current user is admin.

    Args:
        current_user: Current authenticated user

    Returns:
        TokenData if user is admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role not in ["admin", "hr_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )

    return current_user

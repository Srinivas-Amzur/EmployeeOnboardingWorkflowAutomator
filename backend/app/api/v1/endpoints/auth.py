"""
Authentication endpoints (login, logout, register).
"""

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
import httpx

from ....core.security import create_access_token
from ....core.security import TokenData
from ....core.config import get_settings
from ....schemas import (
    ChangePasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    UserCreate,
    UserResponse,
)
from ....services.auth import AuthService
from ...dependencies import DbSession, get_current_user

router = APIRouter(tags=["auth"])
settings = get_settings()


def get_auth_service(db: DbSession) -> AuthService:
    """Dependency to get auth service."""
    return AuthService(db)


@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """
    User login endpoint.

    Args:
        request: Login credentials
        response: Response object for setting cookie
        db: Database session

    Returns:
        Login response with token and user info
    """
    user = await service.authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    # Create token
    token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
    )

    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )

    return LoginResponse(
        access_token=token.access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/google")
async def google_login(
    request: GoogleLoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """Authenticate a user through Google Sign-In token validation."""
    user = await service.authenticate_google_user(request.id_token)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
    )

    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )

    return LoginResponse(
        access_token=token.access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/google/login")
async def google_login_start() -> RedirectResponse:
    """Redirect browser to Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google login is not configured")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    google_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=google_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/google/callback")
async def google_login_callback(
    code: str,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> RedirectResponse:
    """Exchange OAuth code, provision/login user, then redirect to frontend."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google login is not configured")

    async with httpx.AsyncClient(timeout=20.0) as http_client:
        token_response = await http_client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google authorization failed")

    payload = token_response.json()
    id_token_value = payload.get("id_token")
    if not id_token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google token response is missing id_token")

    redirect = RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    user = await service.authenticate_google_user(id_token_value)
    token = create_access_token(subject=str(user.id), email=user.email, role=user.role)
    redirect.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
    return redirect


@router.post("/logout")
async def logout(response: Response) -> dict:
    """
    User logout endpoint.

    Args:
        response: Response object for clearing cookie

    Returns:
        Logout confirmation
    """
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: UserCreate,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """
    User registration endpoint.

    Args:
        request: User creation data
        db: Database session

    Returns:
        Created user
    """
    existing_user = await service.get_user_by_email(request.email)

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await service.create_user(request)

    return UserResponse.model_validate(user)


@router.get("/me")
async def get_current_profile(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Return the current authenticated user's profile."""
    user = await service.get_user_by_id(current_user.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    response: Response,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Change the current authenticated user's password."""
    user = await service.get_user_by_id(current_user.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        updated_user = await service.change_password(user, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = create_access_token(
        subject=str(updated_user.id),
        email=updated_user.email,
        role=updated_user.role,
    )
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )

    return MessageResponse(message="Password updated successfully")

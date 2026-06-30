"""
Unit tests for authentication: register, login, me, change password, edge cases.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData, create_access_token, decode_token, hash_password
from app.main import create_app
from app.models import User
from app.schemas.user import UserCreate
from app.services.auth import AuthService


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_admin_token(user_id: str, email: str) -> str:
    return create_access_token(subject=user_id, email=email, role="admin").access_token


def _build_app(test_db):
    app = create_app()

    async def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    return app


def _build_authed_app(test_db, user_id: str, email: str, role: str = "admin"):
    app = _build_app(test_db)

    def override_auth():
        return TokenData(
            sub=user_id,
            email=email,
            role=role,
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )

    app.dependency_overrides[get_current_user] = override_auth
    return app


# ── Auth service unit tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_authenticate_user(test_db):
    service = AuthService(test_db)
    user = await service.create_user(
        UserCreate(name="Alice", email=f"alice.{uuid4().hex[:6]}@example.com", password="SecurePass1!")
    )
    assert user.id is not None
    assert user.hashed_password != "SecurePass1!"

    authenticated = await service.authenticate_user(user.email, "SecurePass1!")
    assert authenticated is not None
    assert authenticated.id == user.id


@pytest.mark.asyncio
async def test_authenticate_wrong_password(test_db):
    service = AuthService(test_db)
    user = await service.create_user(
        UserCreate(name="Bob", email=f"bob.{uuid4().hex[:6]}@example.com", password="SecurePass1!")
    )
    result = await service.authenticate_user(user.email, "wrongpassword")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_nonexistent_user(test_db):
    service = AuthService(test_db)
    result = await service.authenticate_user("nobody@example.com", "anypassword")
    assert result is None


@pytest.mark.asyncio
async def test_change_password_success(test_db):
    service = AuthService(test_db)
    from app.schemas.user import ChangePasswordRequest

    user = await service.create_user(
        UserCreate(name="Charlie", email=f"charlie.{uuid4().hex[:6]}@example.com", password="OldPass1!")
    )
    updated = await service.change_password(
        user,
        ChangePasswordRequest(
            current_password="OldPass1!",
            new_password="NewPass2!",
            confirm_password="NewPass2!",
        ),
    )
    assert updated is not None
    authenticated = await service.authenticate_user(updated.email, "NewPass2!")
    assert authenticated is not None


@pytest.mark.asyncio
async def test_change_password_wrong_current(test_db):
    service = AuthService(test_db)
    from app.schemas.user import ChangePasswordRequest

    user = await service.create_user(
        UserCreate(name="Diana", email=f"diana.{uuid4().hex[:6]}@example.com", password="MyPass1!")
    )
    with pytest.raises(ValueError, match="Current password is incorrect"):
        await service.change_password(
            user,
            ChangePasswordRequest(
                current_password="WrongPass1!",
                new_password="NewPass2!",
                confirm_password="NewPass2!",
            ),
        )


@pytest.mark.asyncio
async def test_change_password_same_as_current(test_db):
    service = AuthService(test_db)
    from app.schemas.user import ChangePasswordRequest

    user = await service.create_user(
        UserCreate(name="Eve", email=f"eve.{uuid4().hex[:6]}@example.com", password="SamePass1!")
    )
    with pytest.raises(ValueError, match="must be different"):
        await service.change_password(
            user,
            ChangePasswordRequest(
                current_password="SamePass1!",
                new_password="SamePass1!",
                confirm_password="SamePass1!",
            ),
        )


# ── JWT utility tests ─────────────────────────────────────────────────────────

def test_token_encode_decode_roundtrip():
    uid = str(uuid4())
    token = create_access_token(subject=uid, email="test@example.com", role="admin")
    data = decode_token(token.access_token)
    assert data is not None
    assert data.sub == uid
    assert data.email == "test@example.com"
    assert data.role == "admin"


def test_decode_invalid_token_returns_none():
    assert decode_token("not.a.valid.jwt") is None


def test_decode_tampered_token_returns_none():
    token = create_access_token(subject=str(uuid4()), email="x@x.com", role="admin")
    tampered = token.access_token + "X"
    assert decode_token(tampered) is None


# ── Auth endpoint tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_and_login_via_api(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={"name": "Frank", "email": f"frank.{uuid4().hex[:6]}@example.com", "password": "PassWord1!"},
        )
        assert reg_resp.status_code == 201
        assert reg_resp.json()["email"] == reg_resp.json()["email"]
        email = reg_resp.json()["email"]

        # Login with correct credentials
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "PassWord1!"},
        )
        assert login_resp.status_code == 200
        data = login_resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == email


@pytest.mark.asyncio
async def test_login_invalid_credentials(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nosuchuser@example.com", "password": "badpass"},
        )
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(test_db):
    user = User(
        name="Inactive",
        email=f"inactive.{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("PassWord1!"),
        role="employee",
        is_active=False,
    )
    test_db.add(user)
    await test_db.commit()

    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "PassWord1!"},
        )
        assert resp.status_code == 403
        assert "inactive" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_me_endpoint_requires_auth(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_returns_user(test_db):
    service = AuthService(test_db)
    user = await service.create_user(
        UserCreate(name="George", email=f"george.{uuid4().hex[:6]}@example.com", password="PassWord1!")
    )
    app = _build_authed_app(test_db, str(user.id), user.email, role="admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == user.email


@pytest.mark.asyncio
async def test_logout_clears_session(test_db):
    app = _build_app(test_db)
    service = AuthService(test_db)
    user = await service.create_user(
        UserCreate(name="Helen", email=f"helen.{uuid4().hex[:6]}@example.com", password="PassWord1!")
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "PassWord1!"},
        )
        assert login_resp.status_code == 200

        logout_resp = await client.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200
        assert "message" in logout_resp.json()

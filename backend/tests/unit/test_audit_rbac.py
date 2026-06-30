"""Audit log RBAC tests for role-based visibility scopes."""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData
from app.main import create_app
from app.models import User
from app.schemas.employee import EmployeeCreate
from app.services.employee import EmployeeService


def _build_app_with_user(test_db, user_id: str, email: str, role: str):
    app = create_app()

    async def override_db():
        yield test_db

    def override_user():
        return TokenData(
            sub=user_id,
            email=email,
            role=role,
            exp=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    return app


async def _seed_audit_fixture(test_db) -> dict:
    manager_user = User(
        name="Manager User",
        email=f"manager_{uuid4().hex[:6]}@company.com",
        hashed_password=None,
        role="manager",
        is_active=True,
    )
    employee_user = User(
        name="Employee User",
        email=f"employee_{uuid4().hex[:6]}@company.com",
        hashed_password=None,
        role="employee",
        is_active=True,
    )
    hr_admin_user = User(
        name="HR Admin",
        email=f"hr_admin_{uuid4().hex[:6]}@company.com",
        hashed_password=None,
        role="hr_admin",
        is_active=True,
    )
    it_admin_user = User(
        name="IT Admin",
        email=f"it_admin_{uuid4().hex[:6]}@company.com",
        hashed_password=None,
        role="it_admin",
        is_active=True,
    )

    test_db.add_all([manager_user, employee_user, hr_admin_user, it_admin_user])
    await test_db.commit()
    await test_db.refresh(manager_user)
    await test_db.refresh(employee_user)
    await test_db.refresh(hr_admin_user)
    await test_db.refresh(it_admin_user)

    employee_service = EmployeeService(test_db)

    managed_suffix = uuid4().hex[:6]
    unmanaged_suffix = uuid4().hex[:6]

    await employee_service.create_employee(
        EmployeeCreate(
            first_name="Managed",
            last_name="Person",
            email=f"managed_{managed_suffix}@company.com",
            department="Engineering",
            designation="Engineer",
            joining_date=date.today(),
            manager_id=manager_user.id,
        )
    )

    await employee_service.create_employee(
        EmployeeCreate(
            first_name="Unmanaged",
            last_name="Person",
            email=f"unmanaged_{unmanaged_suffix}@company.com",
            department="Finance",
            designation="Analyst",
            joining_date=date.today(),
            manager_id=None,
        )
    )

    await employee_service.create_employee(
        EmployeeCreate(
            first_name="Self",
            last_name="Employee",
            email=employee_user.email,
            department="Support",
            designation="Specialist",
            joining_date=date.today(),
            manager_id=manager_user.id,
        )
    )

    return {
        "manager_user": manager_user,
        "employee_user": employee_user,
        "hr_admin_user": hr_admin_user,
        "it_admin_user": it_admin_user,
        "managed_email_fragment": f"managed_{managed_suffix}@company.com",
        "unmanaged_email_fragment": f"unmanaged_{unmanaged_suffix}@company.com",
    }


@pytest.mark.asyncio
async def test_hr_admin_has_full_audit_access(test_db):
    fixture = await _seed_audit_fixture(test_db)
    user = fixture["hr_admin_user"]

    app = _build_app_with_user(test_db, str(user.id), user.email, "hr_admin")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/audit/logs", params={"limit": 300})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] > 0
    actions = {item["action"] for item in payload["items"]}
    assert "Employee Created" in actions


@pytest.mark.asyncio
async def test_it_admin_gets_operational_audit_access_only(test_db):
    fixture = await _seed_audit_fixture(test_db)
    user = fixture["it_admin_user"]

    app = _build_app_with_user(test_db, str(user.id), user.email, "it_admin")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/audit/logs", params={"limit": 300})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] > 0
    entities = {item["entity"] for item in payload["items"]}
    assert "employee" not in entities


@pytest.mark.asyncio
async def test_manager_gets_limited_visibility_for_managed_scope(test_db):
    fixture = await _seed_audit_fixture(test_db)
    user = fixture["manager_user"]

    app = _build_app_with_user(test_db, str(user.id), user.email, "manager")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/audit/logs", params={"limit": 300})

    assert response.status_code == 200
    payload = response.json()
    details = [item["details"] for item in payload["items"]]

    assert any(fixture["managed_email_fragment"] in item for item in details)
    assert all(fixture["unmanaged_email_fragment"] not in item for item in details)


@pytest.mark.asyncio
async def test_employee_sees_only_own_activity(test_db):
    fixture = await _seed_audit_fixture(test_db)
    user = fixture["employee_user"]

    app = _build_app_with_user(test_db, str(user.id), user.email, "employee")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/audit/logs", params={"limit": 300})

    assert response.status_code == 200
    payload = response.json()
    details = [item["details"] for item in payload["items"]]

    assert any(user.email in item for item in details)
    assert all(fixture["unmanaged_email_fragment"] not in item for item in details)

"""
Unit tests for employee CRUD, onboarding workflow auto-creation, and analytics.
"""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData
from app.main import create_app
from app.models import Employee, OnboardingWorkflow, OnboardingTask
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.employee import EmployeeService
from app.services.analytics import AnalyticsService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_app_with_admin(test_db):
    app = create_app()

    async def override_db():
        yield test_db

    def override_admin():
        return TokenData(
            sub=str(uuid4()),
            email="admin@company.com",
            role="admin",
            exp=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_admin
    return app


def _sample_employee_create(suffix: str | None = None) -> EmployeeCreate:
    s = suffix or uuid4().hex[:8]
    return EmployeeCreate(
        first_name="Test",
        last_name=f"Employee_{s}",
        email=f"emp_{s}@company.com",
        department="Engineering",
        designation="Engineer",
        joining_date=date.today(),
    )


# ── Employee service tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_employee_creates_workflow_and_tasks(test_db):
    service = EmployeeService(test_db)
    emp = await service.create_employee(_sample_employee_create())

    assert emp.id is not None
    assert emp.onboarding_status == "in_progress"

    workflow = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == emp.id)
        )
    ).scalars().first()
    assert workflow is not None
    assert workflow.current_state == "hr_review"

    tasks = (
        await test_db.execute(
            select(OnboardingTask).where(OnboardingTask.workflow_id == workflow.id)
        )
    ).scalars().all()
    assert len(tasks) == 13  # 3 hr_review + 5 provisioning + 3 meetings + 2 documents


@pytest.mark.asyncio
async def test_get_employee_by_id(test_db):
    service = EmployeeService(test_db)
    emp = await service.create_employee(_sample_employee_create())
    found = await service.get_employee(emp.id)
    assert found is not None
    assert found.id == emp.id


@pytest.mark.asyncio
async def test_get_employee_not_found(test_db):
    service = EmployeeService(test_db)
    result = await service.get_employee(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_employee_by_email(test_db):
    service = EmployeeService(test_db)
    emp = await service.create_employee(_sample_employee_create())
    found = await service.get_employee_by_email(emp.email)
    assert found is not None
    assert found.email == emp.email


@pytest.mark.asyncio
async def test_list_employees(test_db):
    service = EmployeeService(test_db)
    await service.create_employee(_sample_employee_create())
    await service.create_employee(_sample_employee_create())
    employees = await service.list_employees()
    assert len(employees) >= 2


@pytest.mark.asyncio
async def test_list_employees_by_department(test_db):
    service = EmployeeService(test_db)
    s = uuid4().hex[:6]
    emp = EmployeeCreate(
        first_name="Dept",
        last_name="Filter",
        email=f"dept_{s}@company.com",
        department=f"Finance_{s}",
        designation="Analyst",
        joining_date=date.today(),
    )
    await service.create_employee(emp)
    results = await service.list_employees(department=f"Finance_{s}")
    assert len(results) == 1
    assert results[0].department == f"Finance_{s}"


@pytest.mark.asyncio
async def test_update_employee(test_db):
    service = EmployeeService(test_db)
    emp = await service.create_employee(_sample_employee_create())
    updated = await service.update_employee(emp.id, EmployeeUpdate(designation="Senior Engineer"))
    assert updated is not None
    assert updated.designation == "Senior Engineer"


@pytest.mark.asyncio
async def test_update_employee_not_found(test_db):
    service = EmployeeService(test_db)
    result = await service.update_employee(uuid4(), EmployeeUpdate(designation="X"))
    assert result is None


# ── Employee API endpoint tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_employee_endpoint(test_db):
    app = _build_app_with_admin(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        s = uuid4().hex[:8]
        resp = await client.post(
            "/api/v1/employees",
            json={
                "first_name": "API",
                "last_name": f"Test_{s}",
                "email": f"api_{s}@company.com",
                "department": "Engineering",
                "designation": "Engineer",
                "joining_date": str(date.today()),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["first_name"] == "API"
        assert "id" in data


@pytest.mark.asyncio
async def test_get_employee_endpoint_not_found(test_db):
    app = _build_app_with_admin(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/employees/{uuid4()}")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_employees_endpoint(test_db):
    service = EmployeeService(test_db)
    await service.create_employee(_sample_employee_create())

    app = _build_app_with_admin(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/employees")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_update_employee_endpoint(test_db):
    service = EmployeeService(test_db)
    emp = await service.create_employee(_sample_employee_create())

    app = _build_app_with_admin(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            f"/api/v1/employees/{emp.id}",
            json={"designation": "Lead Engineer"},
        )
        assert resp.status_code == 200
        assert resp.json()["designation"] == "Lead Engineer"


# ── Analytics service tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_stats_empty(test_db):
    service = AnalyticsService(test_db)
    stats = await service.get_dashboard_stats()
    assert stats["total_workflows"] == 0
    assert stats["total_employees"] == 0
    assert stats["pending_tasks"] == 0
    assert stats["average_completion"] == 0


@pytest.mark.asyncio
async def test_dashboard_stats_with_data(test_db):
    emp_service = EmployeeService(test_db)
    await emp_service.create_employee(_sample_employee_create())

    analytics = AnalyticsService(test_db)
    stats = await analytics.get_dashboard_stats()
    assert stats["total_workflows"] >= 1
    assert stats["total_employees"] >= 1
    assert stats["pending_tasks"] >= 1
    assert stats["workflows_by_state"]["hr_review"] >= 1


@pytest.mark.asyncio
async def test_analytics_dashboard_endpoint(test_db):
    app = _build_app_with_admin(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_workflows" in data
        assert "total_employees" in data
        assert "pending_tasks" in data
        assert "workflows_by_state" in data
        assert "average_completion" in data

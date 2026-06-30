"""RBAC tests for employee portal self-service access model."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData
from app.main import create_app
from app.models import OnboardingWorkflow
from app.schemas.employee import EmployeeCreate
from app.schemas.meeting import MeetingCreate
from app.services.employee import EmployeeService
from app.services.meeting import MeetingService


def _build_app_with_user(test_db, email: str, role: str = "employee"):
    app = create_app()

    async def override_db():
        yield test_db

    def override_user():
        return TokenData(
            sub=str(uuid4()),
            email=email,
            role=role,
            exp=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    return app


async def _create_employee_with_workflow(test_db, email: str):
    employee = await EmployeeService(test_db).create_employee(
        EmployeeCreate(
            first_name="Portal",
            last_name=f"User_{uuid4().hex[:6]}",
            email=email,
            department="Engineering",
            designation="Engineer",
            joining_date=date.today(),
        )
    )
    workflow = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == employee.id)
        )
    ).scalars().first()
    return employee, workflow


@pytest.mark.asyncio
async def test_employee_can_access_own_profile_without_admin(test_db):
    employee_email = f"self_{uuid4().hex[:6]}@company.com"
    employee, _ = await _create_employee_with_workflow(test_db, employee_email)

    app = _build_app_with_user(test_db, email=employee_email, role="employee")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/employees/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(employee.id)
    assert payload["email"].lower() == employee_email.lower()


@pytest.mark.asyncio
async def test_employee_cannot_access_employee_list_endpoint(test_db):
    employee_email = f"list_block_{uuid4().hex[:6]}@company.com"
    await _create_employee_with_workflow(test_db, employee_email)

    app = _build_app_with_user(test_db, email=employee_email, role="employee")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/employees")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_employee_workflow_list_is_forced_to_self_scope(test_db):
    employee_email = f"wf_self_{uuid4().hex[:6]}@company.com"
    other_email = f"wf_other_{uuid4().hex[:6]}@company.com"

    employee, _ = await _create_employee_with_workflow(test_db, employee_email)
    other_employee, _ = await _create_employee_with_workflow(test_db, other_email)

    app = _build_app_with_user(test_db, email=employee_email, role="employee")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/onboarding/workflows",
            params={"employee_id": str(other_employee.id), "limit": 20},
        )

    assert response.status_code == 200
    workflows = response.json()
    assert len(workflows) == 1
    assert workflows[0]["employee_id"] == str(employee.id)


@pytest.mark.asyncio
async def test_employee_meetings_list_is_forced_to_self_scope(test_db):
    employee_email = f"meet_self_{uuid4().hex[:6]}@company.com"
    other_email = f"meet_other_{uuid4().hex[:6]}@company.com"

    employee, workflow = await _create_employee_with_workflow(test_db, employee_email)
    other_employee, other_workflow = await _create_employee_with_workflow(test_db, other_email)

    meeting_service = MeetingService(test_db)
    scheduled_for = datetime.now(timezone.utc) + timedelta(days=1)

    await meeting_service.create_meeting(
        MeetingCreate(
            employee_id=employee.id,
            workflow_id=workflow.id,
            meeting_type="orientation",
            title="Self Orientation",
            description="Self meeting",
            scheduled_for=scheduled_for,
            duration_minutes=60,
            location="Room A",
            meeting_url=None,
            status="scheduled",
        )
    )
    await meeting_service.create_meeting(
        MeetingCreate(
            employee_id=other_employee.id,
            workflow_id=other_workflow.id,
            meeting_type="orientation",
            title="Other Orientation",
            description="Other meeting",
            scheduled_for=scheduled_for,
            duration_minutes=60,
            location="Room B",
            meeting_url=None,
            status="scheduled",
        )
    )

    app = _build_app_with_user(test_db, email=employee_email, role="employee")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/meetings",
            params={"employee_id": str(other_employee.id), "limit": 20},
        )

    assert response.status_code == 200
    meetings = response.json()
    assert len(meetings) == 1
    assert meetings[0]["employee_id"] == str(employee.id)
    assert meetings[0]["title"] == "Self Orientation"


@pytest.mark.asyncio
async def test_employee_can_get_own_meeting_detail(test_db):
    employee_email = f"meet_detail_self_{uuid4().hex[:6]}@company.com"
    employee, workflow = await _create_employee_with_workflow(test_db, employee_email)

    meeting_service = MeetingService(test_db)
    meeting = await meeting_service.create_meeting(
        MeetingCreate(
            employee_id=employee.id,
            workflow_id=workflow.id,
            meeting_type="orientation",
            title="Own Meeting",
            description="Self detail access",
            scheduled_for=datetime.now(timezone.utc) + timedelta(days=2),
            duration_minutes=45,
            location="Room C",
            meeting_url=None,
            status="scheduled",
        )
    )

    app = _build_app_with_user(test_db, email=employee_email, role="employee")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/meetings/{meeting.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(meeting.id)
    assert payload["employee_id"] == str(employee.id)


@pytest.mark.asyncio
async def test_employee_cannot_get_other_meeting_detail(test_db):
    employee_email = f"meet_detail_self_{uuid4().hex[:6]}@company.com"
    other_email = f"meet_detail_other_{uuid4().hex[:6]}@company.com"

    _, _ = await _create_employee_with_workflow(test_db, employee_email)
    other_employee, other_workflow = await _create_employee_with_workflow(test_db, other_email)

    meeting_service = MeetingService(test_db)
    other_meeting = await meeting_service.create_meeting(
        MeetingCreate(
            employee_id=other_employee.id,
            workflow_id=other_workflow.id,
            meeting_type="orientation",
            title="Other Meeting",
            description="Other detail access",
            scheduled_for=datetime.now(timezone.utc) + timedelta(days=2),
            duration_minutes=45,
            location="Room D",
            meeting_url=None,
            status="scheduled",
        )
    )

    app = _build_app_with_user(test_db, email=employee_email, role="employee")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/meetings/{other_meeting.id}")

    assert response.status_code == 404

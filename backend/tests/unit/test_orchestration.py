from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData
from app.main import create_app
from app.models import OnboardingOrchestrationEvent, OnboardingWorkflow
from app.schemas.employee import EmployeeCreate
from app.services.employee import EmployeeService
from app.services.orchestration import OrchestrationService


@pytest.mark.asyncio
async def test_sync_does_not_duplicate_workflow_started_event(test_db):
    employee = await EmployeeService(test_db).create_employee(
        EmployeeCreate(
            first_name="Regression",
            last_name="Guard",
            email=f"regression.{uuid4().hex[:8]}@company.com",
            department="Engineering",
            designation="Platform Engineer",
            joining_date=date.today(),
        )
    )

    workflow = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == employee.id)
        )
    ).scalars().first()

    await OrchestrationService(test_db).sync_workflow_state(workflow.id)

    events = (
        await test_db.execute(
            select(OnboardingOrchestrationEvent)
            .where(OnboardingOrchestrationEvent.workflow_id == workflow.id)
            .order_by(OnboardingOrchestrationEvent.created_at.asc())
        )
    ).scalars().all()

    event_types = [event.event_type for event in events]
    assert event_types.count("workflow_started") == 1
    assert event_types.count("tasks_generated") == 4
    assert workflow.current_state == "hr_review"


@pytest.mark.asyncio
async def test_orchestration_endpoints_return_snapshot_and_events(test_db):
    employee = await EmployeeService(test_db).create_employee(
        EmployeeCreate(
            first_name="API",
            last_name="Observer",
            email=f"observer.{uuid4().hex[:8]}@company.com",
            department="Engineering",
            designation="Platform Engineer",
            joining_date=date.today(),
        )
    )

    workflow = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == employee.id)
        )
    ).scalars().first()

    app = create_app()

    async def override_get_db():
        yield test_db

    def override_get_current_user():
        return TokenData(
            sub=str(uuid4()),
            email="admin@company.com",
            role="admin",
            exp=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        snapshot_response = await client.get(f"/api/v1/onboarding/workflows/{workflow.id}/orchestration")
        events_response = await client.get(f"/api/v1/onboarding/workflows/{workflow.id}/events")

    assert snapshot_response.status_code == 200
    assert events_response.status_code == 200

    snapshot = snapshot_response.json()
    events = events_response.json()

    assert snapshot["workflow_id"] == str(workflow.id)
    assert snapshot["current_state"] == "hr_review"
    assert snapshot["total_tasks"] == 13
    assert snapshot["completed_tasks"] == 0
    assert events[0]["event_type"] == "workflow_started"
    assert sum(event["event_type"] == "tasks_generated" for event in events) == 4
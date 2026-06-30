"""
Unit tests for onboarding workflow tasks, state transitions, progress tracking,
duplicate workflow prevention, and edge cases.
"""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData
from app.main import create_app
from app.models import Employee, Notification, OnboardingTask, OnboardingWorkflow, User
from app.schemas.employee import EmployeeCreate
from app.schemas.onboarding import (
    OnboardingTaskCreate,
    OnboardingTaskUpdate,
    OnboardingWorkflowCreate,
    OnboardingWorkflowUpdate,
)
from app.services.analytics import AnalyticsService
from app.services.employee import EmployeeService
from app.services.onboarding import OnboardingService
from app.services.orchestration import OrchestrationService


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


async def _create_employee_with_workflow(test_db) -> tuple:
    emp = await EmployeeService(test_db).create_employee(
        EmployeeCreate(
            first_name="Workflow",
            last_name=f"Test_{uuid4().hex[:6]}",
            email=f"wf_{uuid4().hex[:6]}@company.com",
            department="Engineering",
            designation="Engineer",
            joining_date=date.today(),
        )
    )
    workflow = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == emp.id)
        )
    ).scalars().first()
    return emp, workflow


# ── Workflow lifecycle tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_created_with_correct_initial_state(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    assert workflow is not None
    assert workflow.current_state == "hr_review"
    assert workflow.completion_percentage == 0
    assert workflow.started_at is not None
    assert workflow.completed_at is None


@pytest.mark.asyncio
async def test_duplicate_workflow_prevention(test_db):
    """Creating same employee twice does not create two workflows for the same employee."""
    emp, workflow1 = await _create_employee_with_workflow(test_db)
    # Simulate sync call (orchestrate_for_employee reuses existing workflow)
    orchestrator = OrchestrationService(test_db)
    workflow2 = await orchestrator.orchestrate_for_employee(emp)

    workflows = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == emp.id)
        )
    ).scalars().all()
    assert len(workflows) == 1
    assert workflow1.id == workflow2.id


@pytest.mark.asyncio
async def test_workflow_progress_zero_on_creation(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)
    progress = await service.get_workflow_progress(workflow.id)

    assert progress["total_tasks"] == 13
    assert progress["completed_tasks"] == 0
    assert progress["pending_tasks"] == 13
    assert progress["completion_percentage"] == 0
    assert progress["current_state"] == "hr_review"


@pytest.mark.asyncio
async def test_workflow_progress_updates_on_task_completion(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    tasks = await service.get_workflow_tasks(workflow.id)
    first_task = tasks[0]
    await service.update_task(first_task.id, OnboardingTaskUpdate(status="completed"))

    progress = await service.get_workflow_progress(workflow.id)
    assert progress["completed_tasks"] == 1
    assert progress["completion_percentage"] > 0


@pytest.mark.asyncio
async def test_workflow_get_and_update(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    found = await service.get_workflow(workflow.id)
    assert found is not None
    assert found.id == workflow.id

    updated = await service.update_workflow(workflow.id, OnboardingWorkflowUpdate(current_state="provisioning"))
    assert updated is not None
    assert updated.current_state == "provisioning"


@pytest.mark.asyncio
async def test_workflow_not_found(test_db):
    service = OnboardingService(test_db)
    result = await service.get_workflow(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_workflow_update_not_found(test_db):
    service = OnboardingService(test_db)
    result = await service.update_workflow(uuid4(), OnboardingWorkflowUpdate(current_state="provisioning"))
    assert result is None


@pytest.mark.asyncio
async def test_list_workflows_filter_by_employee(test_db):
    emp1, _ = await _create_employee_with_workflow(test_db)
    _, _ = await _create_employee_with_workflow(test_db)

    service = OnboardingService(test_db)
    emp1_workflows = await service.get_workflows(employee_id=emp1.id)
    assert len(emp1_workflows) == 1
    assert emp1_workflows[0].employee_id == emp1.id


@pytest.mark.asyncio
async def test_workflow_state_update(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    updated = await service.update_workflow_state(workflow.id, "provisioning")
    assert updated is not None
    assert updated.current_state == "provisioning"


@pytest.mark.asyncio
async def test_workflow_completion_sets_completed_at(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    # Complete all tasks
    tasks = await service.get_workflow_tasks(workflow.id)
    for task in tasks:
        await service.update_task(task.id, OnboardingTaskUpdate(status="completed"))

    updated = await service.update_workflow_state(workflow.id, "completed")
    assert updated is not None
    assert updated.current_state == "completed"
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_workflow_pause_persists_state_timeline_analytics_and_notification(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    actor = User(
        name="Admin Reviewer",
        email=f"admin_{uuid4().hex[:6]}@company.com",
        hashed_password=None,
        role="admin",
        is_active=True,
    )
    test_db.add(actor)
    await test_db.flush()

    updated_workflow, event, _ = await service.apply_workflow_action(
        workflow_id=workflow.id,
        action="pause",
        actor_user_id=actor.id,
        note="Pausing for dependency validation",
    )

    assert updated_workflow is not None
    assert event is not None
    assert updated_workflow.current_state == "paused"

    refreshed_workflow = await service.get_workflow(workflow.id)
    assert refreshed_workflow is not None
    assert refreshed_workflow.current_state == "paused"

    employee_row = (
        await test_db.execute(select(Employee).where(Employee.id == workflow.employee_id))
    ).scalars().first()
    assert employee_row is not None
    assert employee_row.onboarding_status == "paused"

    assert event.event_type == "workflow_paused"
    assert event.state_from == "hr_review"
    assert event.state_to == "paused"

    pause_notification = (
        await test_db.execute(
            select(Notification).where(
                Notification.user_id == actor.id,
                Notification.title == "Workflow paused",
            )
        )
    ).scalars().first()
    assert pause_notification is not None

    dashboard = await AnalyticsService(test_db).get_dashboard_stats()
    assert dashboard["workflows_by_state"].get("paused", 0) == 1
    assert dashboard["employees_by_status"].get("paused", 0) == 1


@pytest.mark.asyncio
async def test_workflow_resume_restores_state_timeline_analytics_and_notification(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    actor = User(
        name="Admin Reviewer",
        email=f"resume_admin_{uuid4().hex[:6]}@company.com",
        hashed_password=None,
        role="admin",
        is_active=True,
    )
    test_db.add(actor)
    await test_db.flush()

    await service.apply_workflow_action(
        workflow_id=workflow.id,
        action="pause",
        actor_user_id=actor.id,
        note="Hold for legal review",
    )

    resumed_workflow, resumed_event, _ = await service.apply_workflow_action(
        workflow_id=workflow.id,
        action="resume",
        actor_user_id=actor.id,
        note="Clear to continue",
    )

    assert resumed_workflow is not None
    assert resumed_event is not None
    assert resumed_workflow.current_state == "hr_review"

    refreshed_workflow = await service.get_workflow(workflow.id)
    assert refreshed_workflow is not None
    assert refreshed_workflow.current_state == "hr_review"

    employee_row = (
        await test_db.execute(select(Employee).where(Employee.id == workflow.employee_id))
    ).scalars().first()
    assert employee_row is not None
    assert employee_row.onboarding_status == "in_progress"

    assert resumed_event.event_type == "workflow_resumed"
    assert resumed_event.state_from == "paused"
    assert resumed_event.state_to == "hr_review"

    resume_notification = (
        await test_db.execute(
            select(Notification).where(
                Notification.user_id == actor.id,
                Notification.title == "Workflow resumed",
            )
        )
    ).scalars().first()
    assert resume_notification is not None

    dashboard = await AnalyticsService(test_db).get_dashboard_stats()
    assert dashboard["workflows_by_state"].get("paused", 0) == 0
    assert dashboard["workflows_by_state"].get("hr_review", 0) == 1
    assert dashboard["employees_by_status"].get("in_progress", 0) == 1


# ── Task management tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_manual_task_to_workflow(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    task = await service.create_task(
        OnboardingTaskCreate(
            workflow_id=workflow.id,
            title="Custom onboarding task",
            description="Manually added task",
            priority="high",
        )
    )
    assert task is not None
    assert task.workflow_id == workflow.id
    assert task.status == "pending"


@pytest.mark.asyncio
async def test_update_task_status_to_completed(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    tasks = await service.get_workflow_tasks(workflow.id)
    task = tasks[0]

    updated = await service.update_task(task.id, OnboardingTaskUpdate(status="completed"))
    assert updated is not None
    assert updated.status == "completed"
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_update_task_status_in_progress(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    tasks = await service.get_workflow_tasks(workflow.id)
    task = tasks[0]

    updated = await service.update_task(task.id, OnboardingTaskUpdate(status="in_progress"))
    assert updated is not None
    assert updated.status == "in_progress"
    assert updated.completed_at is None


@pytest.mark.asyncio
async def test_update_task_not_found(test_db):
    service = OnboardingService(test_db)
    result = await service.update_task(uuid4(), OnboardingTaskUpdate(status="completed"))
    assert result is None


@pytest.mark.asyncio
async def test_get_tasks_for_workflow(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)

    tasks = await service.get_workflow_tasks(workflow.id)
    assert len(tasks) == 13
    statuses = {t.status for t in tasks}
    assert statuses == {"pending"}


# ── Workflow API endpoint tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_workflow_endpoint(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    app = _build_app_with_admin(test_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{workflow.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(workflow.id)
        assert data["current_state"] == "hr_review"


@pytest.mark.asyncio
async def test_get_workflow_not_found_endpoint(test_db):
    app = _build_app_with_admin(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{uuid4()}")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_workflow_tasks_endpoint(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    app = _build_app_with_admin(test_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{workflow.id}/tasks")
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 13


@pytest.mark.asyncio
async def test_update_task_status_endpoint(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    service = OnboardingService(test_db)
    tasks = await service.get_workflow_tasks(workflow.id)
    task_id = str(tasks[0].id)

    app = _build_app_with_admin(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/onboarding/tasks/{task_id}",
            json={"status": "completed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_workflow_progress_endpoint(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    app = _build_app_with_admin(test_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{workflow.id}/progress")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_tasks"] == 13
        assert data["completion_percentage"] == 0


@pytest.mark.asyncio
async def test_orchestration_snapshot_endpoint(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    app = _build_app_with_admin(test_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{workflow.id}/orchestration")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_id"] == str(workflow.id)
        assert data["current_state"] == "hr_review"
        assert data["total_tasks"] == 13


@pytest.mark.asyncio
async def test_orchestration_events_endpoint(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    app = _build_app_with_admin(test_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{workflow.id}/events")
        assert resp.status_code == 200
        events = resp.json()
        event_types = [e["event_type"] for e in events]
        assert "workflow_started" in event_types
        assert event_types.count("workflow_started") == 1


@pytest.mark.asyncio
async def test_add_task_workflow_id_mismatch(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    app = _build_app_with_admin(test_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/onboarding/workflows/{workflow.id}/tasks",
            json={
                "title": "Mismatch task",
                "workflow_id": str(uuid4()),  # Different from path workflow_id
            },
        )
        assert resp.status_code == 400
        assert "mismatch" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_sync_workflow_state(test_db):
    _, workflow = await _create_employee_with_workflow(test_db)
    orchestrator = OrchestrationService(test_db)
    refreshed = await orchestrator.sync_workflow_state(workflow.id)
    assert refreshed is not None
    assert refreshed.current_state == "hr_review"


@pytest.mark.asyncio
async def test_sync_workflow_state_not_found(test_db):
    orchestrator = OrchestrationService(test_db)
    result = await orchestrator.sync_workflow_state(uuid4())
    assert result is None

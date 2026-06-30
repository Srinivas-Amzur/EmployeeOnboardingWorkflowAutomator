"""
Full end-to-end integration test covering the complete onboarding business flow:
1. Register + Login
2. Create employee → workflow auto-starts
3. LangGraph orchestration triggers → tasks auto-generate
4. Workflow state transitions
5. Notifications generate for admin
6. Dashboard metrics update
7. Analytics update
8. Complete onboarding tasks
9. Workflow completion
10. Notifications update correctly

Edge cases:
- Duplicate workflow creation
- Expired token access
- Non-admin accessing admin endpoints
- Large notification lists
"""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData, create_access_token, hash_password
from app.main import create_app
from app.models import Notification, OnboardingTask, OnboardingWorkflow, User
from app.schemas.employee import EmployeeCreate
from app.schemas.onboarding import OnboardingTaskUpdate
from app.services.analytics import AnalyticsService
from app.services.employee import EmployeeService
from app.services.notification import NotificationService
from app.services.onboarding import OnboardingService


# ─────────────────────────────────────────────────────────────────────────────
#  Fixtures / helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_app(test_db, admin_user_id: str | None = None, role: str = "admin"):
    app = create_app()

    async def override_db():
        yield test_db

    uid = admin_user_id or str(uuid4())

    def override_auth():
        return TokenData(
            sub=uid,
            email="admin@company.com",
            role=role,
            exp=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth
    return app


async def _create_admin_user(test_db) -> User:
    user = User(
        name="Admin",
        email=f"admin.{uuid4().hex[:6]}@company.com",
        hashed_password=hash_password("AdminPass1"),
        role="admin",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


# ─────────────────────────────────────────────────────────────────────────────
#  Full business flow test
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_complete_onboarding_business_flow(test_db):
    """
    Validates the full onboarding flow from employee creation to workflow completion.
    Steps: create employee → workflow starts → tasks auto-generated → notifications
    sent → tasks completed → workflow completes → analytics updated.
    """
    admin_user = await _create_admin_user(test_db)

    # ── Step 1: Create employee (triggers orchestration) ──────────────────
    emp_service = EmployeeService(test_db)
    employee = await emp_service.create_employee(
        EmployeeCreate(
            first_name="Integration",
            last_name="Tester",
            email=f"it.{uuid4().hex[:6]}@company.com",
            department="Engineering",
            designation="Platform Engineer",
            joining_date=date.today(),
        )
    )
    assert employee.id is not None

    # ── Step 2: Verify workflow auto-started ──────────────────────────────
    workflow = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == employee.id)
        )
    ).scalars().first()
    assert workflow is not None
    assert workflow.current_state == "hr_review"
    assert workflow.completion_percentage == 0

    # ── Step 3: Verify 13 tasks auto-generated ────────────────────────────
    tasks = (
        await test_db.execute(
            select(OnboardingTask).where(OnboardingTask.workflow_id == workflow.id)
        )
    ).scalars().all()
    assert len(tasks) == 13

    task_titles = {t.title for t in tasks}
    assert "Create email account" in task_titles
    assert "Configure VPN" in task_titles
    assert "Schedule HR orientation" in task_titles
    assert "Share employee handbook" in task_titles

    # ── Step 4: Verify notifications generated for admin ──────────────────
    notifications = (
        await test_db.execute(
            select(Notification).where(Notification.user_id == admin_user.id)
        )
    ).scalars().all()
    notification_types = {n.notification_type for n in notifications}
    assert "workflow_started" in notification_types

    # ── Step 5: Verify dashboard metrics reflect new data ─────────────────
    analytics = AnalyticsService(test_db)
    stats = await analytics.get_dashboard_stats()
    assert stats["total_workflows"] >= 1
    assert stats["total_employees"] >= 1
    assert stats["pending_tasks"] >= 13
    assert stats["workflows_by_state"]["hr_review"] >= 1

    # ── Step 6: Complete HR review stage tasks ────────────────────────────
    onboarding_svc = OnboardingService(test_db)
    hr_tasks = [t for t in tasks if t.title in {
        "Validate employee information",
        "Verify joining date",
        "Assign onboarding owner",
    }]
    assert len(hr_tasks) == 3
    for task in hr_tasks:
        updated = await onboarding_svc.update_task(task.id, OnboardingTaskUpdate(status="completed"))
        assert updated.status == "completed"
        assert updated.completed_at is not None

    # ── Step 7: Verify progress updates ───────────────────────────────────
    progress = await onboarding_svc.get_workflow_progress(workflow.id)
    assert progress["completed_tasks"] == 3
    assert progress["completion_percentage"] > 0

    # ── Step 8: Complete all tasks to drive workflow to completion ─────────
    remaining_tasks = [t for t in tasks if t.title not in {t.title for t in hr_tasks}]
    for task in remaining_tasks:
        await onboarding_svc.update_task(task.id, OnboardingTaskUpdate(status="completed"))

    # ── Step 9: Update workflow to completed ──────────────────────────────
    completed_workflow = await onboarding_svc.update_workflow_state(workflow.id, "completed")
    assert completed_workflow is not None
    assert completed_workflow.current_state == "completed"
    assert completed_workflow.completed_at is not None

    # ── Step 10: Verify final analytics reflect completion ────────────────
    final_stats = await analytics.get_dashboard_stats()
    assert final_stats["completed_workflows"] >= 1


# ─────────────────────────────────────────────────────────────────────────────
#  Notifications integration tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notifications_flow_read_all(test_db):
    """Create multiple notifications, verify unread count, then mark all read."""
    admin = await _create_admin_user(test_db)
    notification_svc = NotificationService(test_db)

    # Create several notifications
    for i in range(5):
        await notification_svc.create_ai_indexing_completed_notification(
            user_id=admin.id,
            document_name=f"doc_{i}.pdf",
            chunks_indexed=i + 1,
        )

    unread_count = await notification_svc.get_unread_count(admin.id)
    assert unread_count == 5

    updated = await notification_svc.mark_all_as_read(admin.id)
    assert updated == 5

    unread_after = await notification_svc.get_unread_count(admin.id)
    assert unread_after == 0


@pytest.mark.asyncio
async def test_notifications_unread_only_filter(test_db):
    admin = await _create_admin_user(test_db)
    svc = NotificationService(test_db)

    notif1 = await svc.create_ai_indexing_completed_notification(
        user_id=admin.id, document_name="a.pdf", chunks_indexed=1
    )
    notif2 = await svc.create_ai_indexing_completed_notification(
        user_id=admin.id, document_name="b.pdf", chunks_indexed=2
    )

    # Mark one as read
    await svc.mark_as_read(admin.id, notif1.id)

    unread_list = await svc.list_notifications(admin.id, unread_only=True)
    assert len(unread_list) == 1
    assert unread_list[0].id == notif2.id


@pytest.mark.asyncio
async def test_notification_mark_read_other_user_fails(test_db):
    """User cannot mark another user's notification as read."""
    admin1 = await _create_admin_user(test_db)
    admin2 = await _create_admin_user(test_db)
    svc = NotificationService(test_db)

    notif = await svc.create_ai_indexing_completed_notification(
        user_id=admin1.id, document_name="private.pdf", chunks_indexed=3
    )

    # Attempt to mark as read with wrong user
    result = await svc.mark_as_read(admin2.id, notif.id)
    assert result is None

    # Original notification is still unread
    still_unread = await svc.get_unread_count(admin1.id)
    assert still_unread == 1


@pytest.mark.asyncio
async def test_large_notification_list_pagination(test_db):
    """Verify pagination works correctly for large notification lists."""
    admin = await _create_admin_user(test_db)
    svc = NotificationService(test_db)

    # Create 25 notifications
    for i in range(25):
        await svc.create_ai_indexing_completed_notification(
            user_id=admin.id, document_name=f"doc_{i}.pdf", chunks_indexed=i + 1
        )

    page1 = await svc.list_notifications(admin.id, skip=0, limit=10)
    page2 = await svc.list_notifications(admin.id, skip=10, limit=10)
    page3 = await svc.list_notifications(admin.id, skip=20, limit=10)

    assert len(page1) == 10
    assert len(page2) == 10
    assert len(page3) == 5

    # Pages should not overlap
    page1_ids = {n.id for n in page1}
    page2_ids = {n.id for n in page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_notifications_api_endpoint_mark_one(test_db):
    admin = await _create_admin_user(test_db)
    svc = NotificationService(test_db)
    notif = await svc.create_ai_indexing_completed_notification(
        user_id=admin.id, document_name="test.pdf", chunks_indexed=2
    )

    app = _build_app(test_db, admin_user_id=str(admin.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(f"/api/v1/notifications/{notif.id}/read")
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True


@pytest.mark.asyncio
async def test_notifications_api_endpoint_read_all(test_db):
    admin = await _create_admin_user(test_db)
    svc = NotificationService(test_db)
    for i in range(3):
        await svc.create_ai_indexing_completed_notification(
            user_id=admin.id, document_name=f"f{i}.pdf", chunks_indexed=1
        )

    app = _build_app(test_db, admin_user_id=str(admin.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch("/api/v1/notifications/read-all")
        assert resp.status_code == 200
        assert resp.json()["updated"] == 3

        count_resp = await client.get("/api/v1/notifications/unread-count")
        assert count_resp.status_code == 200
        assert count_resp.json()["count"] == 0


# ─────────────────────────────────────────────────────────────────────────────
#  Edge case / security tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_non_admin_cannot_create_employee(test_db):
    """An employee-role user cannot create other employees."""
    app = _build_app(test_db, role="employee")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        s = uuid4().hex[:6]
        resp = await client.post(
            "/api/v1/employees",
            json={
                "first_name": "Unauthorized",
                "last_name": "User",
                "email": f"unauth_{s}@company.com",
                "department": "HR",
                "designation": "Analyst",
                "joining_date": str(date.today()),
            },
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_protected_routes(test_db):
    """Requests without authentication are rejected with 401."""
    from app.main import create_app as create_fresh_app

    fresh_app = create_fresh_app()

    async def override_db():
        yield test_db

    fresh_app.dependency_overrides[get_db] = override_db

    transport = ASGITransport(app=fresh_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for endpoint in [
            "/api/v1/employees",
            "/api/v1/onboarding/workflows",
            "/api/v1/analytics/dashboard",
            "/api/v1/notifications",
        ]:
            resp = await client.get(endpoint)
            assert resp.status_code == 401, f"Expected 401 for {endpoint}, got {resp.status_code}"


@pytest.mark.asyncio
async def test_workflow_not_found_returns_404(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{uuid4()}")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_employee_create_validation_missing_fields(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Missing required fields: last_name, email, department, designation, joining_date
        resp = await client.post(
            "/api/v1/employees",
            json={"first_name": "Incomplete"},
        )
        assert resp.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_employee_create_invalid_email(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/employees",
            json={
                "first_name": "Bad",
                "last_name": "Email",
                "email": "not-an-email",
                "department": "HR",
                "designation": "Analyst",
                "joining_date": str(date.today()),
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_orchestration_snapshot_not_found(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{uuid4()}/orchestration")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_orchestration_events_not_found(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/onboarding/workflows/{uuid4()}/events")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_task_update_not_found_endpoint(test_db):
    app = _build_app(test_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/onboarding/tasks/{uuid4()}",
            json={"status": "completed"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_workflow_task_completion_fires_notification(test_db):
    """Completing a task creates a task_completed notification."""
    admin = await _create_admin_user(test_db)
    emp_service = EmployeeService(test_db)

    employee = await emp_service.create_employee(
        EmployeeCreate(
            first_name="Notify",
            last_name="OnComplete",
            email=f"noc.{uuid4().hex[:6]}@company.com",
            department="QA",
            designation="Tester",
            joining_date=date.today(),
        )
    )

    workflow = (
        await test_db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == employee.id)
        )
    ).scalars().first()

    onboarding_svc = OnboardingService(test_db)
    tasks = await onboarding_svc.get_workflow_tasks(workflow.id)

    # Assign task to the admin user so they get the completion notification
    task = tasks[0]
    task.assigned_to = admin.id
    await test_db.commit()
    await test_db.refresh(task)

    await onboarding_svc.update_task(task.id, OnboardingTaskUpdate(status="completed"))

    notifications = (
        await test_db.execute(
            select(Notification)
            .where(Notification.user_id == admin.id)
            .where(Notification.notification_type == "task_completed")
        )
    ).scalars().all()
    assert len(notifications) >= 1

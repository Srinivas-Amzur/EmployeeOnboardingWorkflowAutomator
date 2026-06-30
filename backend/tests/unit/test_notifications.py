from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData
from app.main import create_app
from app.models import Notification, User
from app.schemas.employee import EmployeeCreate
from app.services.employee import EmployeeService
from app.services.notification import NotificationService


@pytest.mark.asyncio
async def test_notification_service_crud(test_db):
    user = User(
        name="Notifier",
        email=f"notifier.{uuid4().hex[:8]}@company.com",
        role="admin",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    service = NotificationService(test_db)
    created = await service.create_ai_indexing_completed_notification(
        user_id=user.id,
        document_name="onboarding-handbook.pdf",
        chunks_indexed=4,
    )

    assert created.notification_type == "ai_indexing_completed"

    unread_count = await service.get_unread_count(user.id)
    assert unread_count == 1

    marked = await service.mark_as_read(user.id, created.id)
    assert marked is not None
    assert marked.is_read is True


@pytest.mark.asyncio
async def test_notification_endpoints_and_orchestration_trigger(test_db):
    admin = User(
        name="Admin User",
        email=f"admin.{uuid4().hex[:8]}@company.com",
        role="admin",
        is_active=True,
    )
    manager = User(
        name="Manager User",
        email=f"manager.{uuid4().hex[:8]}@company.com",
        role="manager",
        is_active=True,
    )
    test_db.add(admin)
    test_db.add(manager)
    await test_db.commit()
    await test_db.refresh(admin)
    await test_db.refresh(manager)

    await EmployeeService(test_db).create_employee(
        EmployeeCreate(
            first_name="Notify",
            last_name="Employee",
            email=f"employee.{uuid4().hex[:8]}@company.com",
            department="Engineering",
            designation="Platform Engineer",
            joining_date=date.today(),
            manager_id=manager.id,
        )
    )

    notifications_for_admin = (
        await test_db.execute(select(Notification).where(Notification.user_id == admin.id))
    ).scalars().all()
    assert len(notifications_for_admin) >= 2
    assert any(item.notification_type == "workflow_started" for item in notifications_for_admin)

    app = create_app()

    async def override_get_db():
        yield test_db

    def override_get_current_user():
        return TokenData(
            sub=str(admin.id),
            email=admin.email,
            role="admin",
            exp=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get("/api/v1/notifications")
        count_response = await client.get("/api/v1/notifications/unread-count")

        assert list_response.status_code == 200
        assert count_response.status_code == 200

        items = list_response.json()["items"]
        assert len(items) >= 1
        first_notification_id = items[0]["id"]

        mark_one_response = await client.patch(f"/api/v1/notifications/{first_notification_id}/read")
        mark_all_response = await client.patch("/api/v1/notifications/read-all")

    assert mark_one_response.status_code == 200
    assert mark_all_response.status_code == 200
    assert mark_all_response.json()["updated"] >= 0

"""
Directly runs the full onboarding orchestration for employee 3b045a6d-504c-4340-9372-3a0cdc1e1739
so we can see the actual error and fix it, then verify all outputs.
"""
import asyncio, sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

EMP_ID = "3b045a6d-504c-4340-9372-3a0cdc1e1739"

async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.employee import Employee
    from app.services.orchestration import OrchestrationService
    from app.services.notification import NotificationService
    from sqlalchemy import select, text
    from uuid import UUID

    async with AsyncSessionLocal() as db:
        # Get employee
        result = await db.execute(select(Employee).where(Employee.id == UUID(EMP_ID)))
        employee = result.scalars().first()
        if not employee:
            print("ERROR: Employee not found!")
            return

        print(f"Found employee: {employee.first_name} {employee.last_name} ({employee.email})")
        print(f"Status: {employee.onboarding_status}")
        print()

        # Run orchestration
        print("Running orchestration...")
        try:
            orchestrator = OrchestrationService(db)
            workflow = await orchestrator.orchestrate_for_employee(employee)
            print(f"SUCCESS! Workflow ID: {workflow.id}")
            print(f"State: {workflow.current_state}")
            print(f"Progress: {workflow.completion_percentage}%")
        except Exception as e:
            print(f"ORCHESTRATION ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()
            return

        # Show tasks
        from sqlalchemy import select as sel
        from app.models.task import OnboardingTask
        from app.models.meeting import OnboardingMeeting
        from app.models.notification import Notification

        tasks_result = await db.execute(
            sel(OnboardingTask).where(OnboardingTask.workflow_id == workflow.id)
        )
        tasks = tasks_result.scalars().all()
        print(f"\nTASKS ({len(tasks)}):")
        for t in tasks:
            print(f"  [{t.priority.upper():6}] {t.status:12} {t.title}")

        notifs_result = await db.execute(
            sel(Notification).order_by(Notification.created_at.desc()).limit(20)
        )
        notifs = notifs_result.scalars().all()
        print(f"\nNOTIFICATIONS ({len(notifs)}):")
        for n in notifs:
            print(f"  [{n.notification_type:30}] {n.title}")

asyncio.run(main())

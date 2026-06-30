"""Send the onboarding documents email to Srinivas Katta right now."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

EMP_ID = "3b045a6d-504c-4340-9372-3a0cdc1e1739"

async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.employee import Employee
    from app.services.notification import NotificationService
    from sqlalchemy import select
    from uuid import UUID

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Employee).where(Employee.id == UUID(EMP_ID)))
        employee = result.scalars().first()

        svc = NotificationService(db)

        print(f"Sending documents email to: {employee.email}")
        await svc.send_documents_email(
            employee_email=employee.email,
            employee_name=f"{employee.first_name} {employee.last_name}",
            company_email=employee.company_email or f"{employee.first_name.lower()}.{employee.last_name.lower()}@amzur.com",
            department=employee.department,
            manager_id=employee.manager_id,
        )
        print("Sent.")

        # Also resend welcome email with updated domain
        print(f"Resending welcome email to: {employee.email}")
        await svc.send_welcome_email(
            employee_email=employee.email,
            employee_name=f"{employee.first_name} {employee.last_name}",
            employee_id=str(employee.id),
            company_email=f"srinivas.katta@amzur.com",
            department=employee.department,
            designation=employee.designation,
            manager_id=employee.manager_id,
            joining_date=str(employee.joining_date),
            workflow_status="hr_review",
        )
        print("Sent.")

        # Update company_email in DB to use amzur.com domain
        employee.company_email = "srinivas.katta@amzur.com"
        await db.commit()
        print(f"Updated company_email -> srinivas.katta@amzur.com")

asyncio.run(main())

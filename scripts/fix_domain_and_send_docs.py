"""
1. Fix all @company.local company_email values → @amzur.com
2. Send welcome email + documents email to every employee currently in DB
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.employee import Employee
    from app.services.notification import NotificationService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Employee))
        employees = result.scalars().all()

        if not employees:
            print("No employees in DB. Create one via the app first.")
            return

        svc = NotificationService(db)

        for emp in employees:
            old_email = emp.company_email or ""

            # Fix domain
            if "@company.local" in old_email:
                new_email = old_email.replace("@company.local", "@amzur.com")
                emp.company_email = new_email
                print(f"Fixed: {old_email} -> {new_email}")
            elif not old_email:
                new_email = f"{emp.first_name.lower()}.{emp.last_name.lower()}@amzur.com"
                emp.company_email = new_email
                print(f"Set:   (none) -> {new_email}")
            else:
                new_email = emp.company_email
                print(f"OK:    {new_email} (no change)")

        await db.commit()
        print("DB updated.\n")

        # Re-query to get refreshed data
        result2 = await db.execute(select(Employee))
        employees = result2.scalars().all()

        for emp in employees:
            name  = f"{emp.first_name} {emp.last_name}"
            cemail = emp.company_email or f"{emp.first_name.lower()}.{emp.last_name.lower()}@amzur.com"

            print(f"\nSending emails to: {emp.email} ({name})")

            # Welcome email
            print(f"  [1/2] Welcome email...")
            await svc.send_welcome_email(
                employee_email=emp.email,
                employee_name=name,
                employee_id=str(emp.id),
                company_email=cemail,
                department=emp.department,
                designation=emp.designation,
                manager_id=emp.manager_id,
                joining_date=str(emp.joining_date),
                workflow_status=emp.onboarding_status,
            )
            print(f"        Sent.")

            # Onboarding documents email
            print(f"  [2/2] Documents email...")
            await svc.send_documents_email(
                employee_email=emp.email,
                employee_name=name,
                company_email=cemail,
                department=emp.department,
                manager_id=emp.manager_id,
            )
            print(f"        Sent.")

        print("\nDone.")

asyncio.run(main())

"""
Employee service for employee management.
"""

import re
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Employee
from ..schemas.employee import EmployeeCreate, EmployeeUpdate
from .orchestration import OrchestrationService
from .base import BaseService
from .notification import NotificationService


def _generate_company_email(first_name: str, last_name: str) -> str:
    """Generate a company email address from employee name."""
    def _normalize(name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r"[^a-z0-9]", ".", name)
        name = re.sub(r"\.+", ".", name).strip(".")
        return name

    return f"{_normalize(first_name)}.{_normalize(last_name)}@amzur.com"


class EmployeeService(BaseService):
    """Service for managing employees."""

    async def create_employee(
        self, request: EmployeeCreate
    ) -> Employee:
        """
        Create a new employee.

        Args:
            request: Employee creation request

        Returns:
            Created employee
        """
        company_email = _generate_company_email(request.first_name, request.last_name)

        employee = Employee(**request.model_dump())
        employee.company_email = company_email
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        self.logger.info(
            "employee_created",
            extra={
                "employee_id": str(employee.id),
                "employee_email": employee.email,
                "company_email": employee.company_email,
                "department": employee.department,
            },
        )

        orchestrator = OrchestrationService(self.db)
        workflow = await orchestrator.orchestrate_for_employee(employee)
        self.logger.info(
            "workflow_started",
            extra={
                "employee_id": str(employee.id),
                "workflow_id": str(workflow.id),
                "workflow_state": workflow.current_state,
                "completion_percentage": workflow.completion_percentage,
            },
        )

        notification_service = NotificationService(self.db)
        await notification_service.send_welcome_email(
            employee_email=employee.email,
            employee_name=f"{employee.first_name} {employee.last_name}",
            employee_id=str(employee.id),
            company_email=company_email,
            department=employee.department,
            designation=employee.designation,
            manager_id=employee.manager_id,
            joining_date=str(employee.joining_date),
            workflow_status=workflow.current_state,
        )

        await self.db.refresh(employee)
        return employee

    async def get_employee(self, employee_id: UUID | str) -> Employee | None:
        """
        Get an employee by ID.

        Args:
            employee_id: Employee ID (UUID or string)

        Returns:
            Employee or None if not found
        """
        if isinstance(employee_id, str):
            try:
                employee_id = UUID(employee_id)
            except (ValueError, TypeError):
                return None
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_employee_by_email(self, email: str) -> Employee | None:
        """
        Get an employee by email.

        Args:
            email: Employee email

        Returns:
            Employee or None if not found
        """
        stmt = select(Employee).where(Employee.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_employees(
        self,
        department: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Employee]:
        """
        List employees with optional filtering.

        Args:
            department: Filter by department
            status: Filter by onboarding status
            skip: Skip count for pagination
            limit: Limit for pagination

        Returns:
            List of employees
        """
        stmt = select(Employee)

        if department:
            stmt = stmt.where(Employee.department == department)

        if status:
            stmt = stmt.where(Employee.onboarding_status == status)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_employee(
        self, employee_id: UUID | str, request: EmployeeUpdate
    ) -> Employee | None:
        """
        Update an employee.

        Args:
            employee_id: Employee ID (UUID or string)
            request: Update request

        Returns:
            Updated employee or None if not found
        """
        employee = await self.get_employee(employee_id)
        if not employee:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)

        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def update_onboarding_status(
        self, employee_id: UUID, status: str
    ) -> Employee | None:
        """
        Update employee onboarding status.

        Args:
            employee_id: Employee ID
            status: New onboarding status

        Returns:
            Updated employee or None if not found
        """
        employee = await self.get_employee(employee_id)
        if not employee:
            return None

        employee.onboarding_status = status
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def get_employees_joining_soon(
        self, days_ahead: int = 30
    ) -> list[Employee]:
        """
        Get employees joining in the next N days.

        Args:
            days_ahead: Number of days ahead to check

        Returns:
            List of employees joining soon
        """
        from datetime import datetime, timedelta

        future_date = date.today() + timedelta(days=days_ahead)
        stmt = (
            select(Employee)
            .where(
                (Employee.joining_date <= future_date)
                & (Employee.joining_date >= date.today())
            )
            .where(Employee.onboarding_status == "pending")
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_department_stats(self) -> dict:
        """
        Get statistics by department.

        Returns:
            Dictionary with department statistics
        """
        stmt = select(Employee)
        result = await self.db.execute(stmt)
        all_employees = result.scalars().all()

        stats = {}
        for employee in all_employees:
            if employee.department not in stats:
                stats[employee.department] = {
                    "total": 0,
                    "pending": 0,
                    "in_progress": 0,
                    "completed": 0,
                }

            stats[employee.department]["total"] += 1
            stats[employee.department][employee.onboarding_status] = (
                stats[employee.department].get(employee.onboarding_status, 0) + 1
            )

        return stats

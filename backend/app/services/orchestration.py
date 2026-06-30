"""
Service layer for LangGraph-driven onboarding orchestration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select

from ..ai.orchestrator import (
    DEFAULT_TASK_BLUEPRINTS,
    create_onboarding_orchestrator,
)
from ..core.logging import get_logger
from ..models import Employee, OnboardingOrchestrationEvent, OnboardingTask, OnboardingWorkflow, User
from ..services.notification import NotificationService
from .base import BaseService

logger = get_logger(__name__)


class OrchestrationService(BaseService):
    """Coordinates workflow creation, task automation, and state synchronization."""

    def __init__(self, db):
        super().__init__(db)
        self.notification_service = NotificationService(db)
        self.graph = create_onboarding_orchestrator()

    async def orchestrate_for_employee(self, employee: Employee) -> OnboardingWorkflow:
        """Bootstrap onboarding for a newly created employee."""
        workflow, is_new_workflow = await self._ensure_workflow(employee)
        tasks = await self._get_workflow_tasks(workflow.id)

        graph_state = self._build_graph_state(employee, workflow, tasks, is_new_workflow=is_new_workflow)
        result = self.graph.invoke(graph_state)

        created_tasks = await self._apply_task_blueprints(workflow.id, result["task_blueprints"])
        await self.db.flush()

        updated_tasks = tasks + created_tasks
        final_state = self._build_graph_state(employee, workflow, updated_tasks, is_new_workflow=False)
        final_state["current_state"] = result["current_state"]
        final_state["completion_percentage"] = result["completion_percentage"]
        final_result = self.graph.invoke(final_state)

        await self._apply_workflow_state(employee, workflow, final_result)
        await self._persist_events(employee.id, workflow.id, result["events"])
        await self._persist_events(employee.id, workflow.id, final_result["events"])
        await self._persist_events(employee.id, workflow.id, final_result["escalations"])
        recipients = await self._resolve_notification_recipients(employee)
        all_events = result["events"] + final_result["events"] + final_result["escalations"]
        await self.notification_service.create_workflow_event_notifications(
            recipient_ids=recipients,
            employee_name=f"{employee.first_name} {employee.last_name}",
            workflow_id=workflow.id,
            events=all_events,
            commit=False,
        )
        await self.notification_service.create_task_assignment_notifications(created_tasks, commit=False)
        await self.db.commit()
        await self.db.refresh(workflow)

        self._send_notifications(employee, result["notifications"] + final_result["notifications"])
        if is_new_workflow:
            await self._send_milestone_email(employee, "initiated")
        logger.info(
            "Onboarding orchestration completed for employee=%s workflow=%s state=%s progress=%s",
            employee.id,
            workflow.id,
            workflow.current_state,
            workflow.completion_percentage,
        )
        return workflow

    async def sync_workflow_state(self, workflow_id: UUID) -> OnboardingWorkflow | None:
        """Recalculate workflow state and escalations after task mutations."""
        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            return None

        employee = await self._get_employee(workflow.employee_id)
        if not employee:
            return None

        previous_state = workflow.current_state
        tasks = await self._get_workflow_tasks(workflow.id)
        graph_state = self._build_graph_state(employee, workflow, tasks, is_new_workflow=False)
        result = self.graph.invoke(graph_state)

        await self._apply_workflow_state(employee, workflow, result)
        await self._persist_events(employee.id, workflow.id, result["events"])
        await self._persist_events(employee.id, workflow.id, result["escalations"])
        recipients = await self._resolve_notification_recipients(employee)
        await self.notification_service.create_workflow_event_notifications(
            recipient_ids=recipients,
            employee_name=f"{employee.first_name} {employee.last_name}",
            workflow_id=workflow.id,
            events=result["events"] + result["escalations"],
            commit=False,
        )
        await self.db.commit()
        await self.db.refresh(workflow)

        self._send_notifications(employee, result["notifications"])
        if workflow.current_state != previous_state:
            await self._send_milestone_email(employee, workflow.current_state)
        return workflow

    async def get_workflow_snapshot(self, workflow_id: UUID) -> dict[str, Any] | None:
        """Return the current orchestration snapshot for a workflow."""
        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            return None

        tasks = await self._get_workflow_tasks(workflow_id)
        completed_tasks = sum(task.status == "completed" for task in tasks)

        return {
            "workflow_id": workflow.id,
            "employee_id": workflow.employee_id,
            "current_state": workflow.current_state,
            "completion_percentage": workflow.completion_percentage,
            "total_tasks": len(tasks),
            "completed_tasks": completed_tasks,
        }

    async def get_workflow_events(self, workflow_id: UUID) -> list[OnboardingOrchestrationEvent] | None:
        """Return orchestration audit events for a workflow, oldest first."""
        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            return None

        result = await self.db.execute(
            select(OnboardingOrchestrationEvent)
            .where(OnboardingOrchestrationEvent.workflow_id == workflow_id)
            .order_by(OnboardingOrchestrationEvent.created_at.asc())
        )
        return list(result.scalars().all())

    async def _ensure_workflow(self, employee: Employee) -> tuple[OnboardingWorkflow, bool]:
        result = await self.db.execute(
            select(OnboardingWorkflow).where(OnboardingWorkflow.employee_id == employee.id)
        )
        workflow = result.scalars().first()
        if workflow:
            return workflow, False

        workflow = OnboardingWorkflow(
            employee_id=employee.id,
            current_state="initiated",
            completion_percentage=0,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(workflow)
        await self.db.flush()
        return workflow, True

    async def _get_workflow(self, workflow_id: UUID) -> OnboardingWorkflow | None:
        result = await self.db.execute(select(OnboardingWorkflow).where(OnboardingWorkflow.id == workflow_id))
        return result.scalars().first()

    async def _get_employee(self, employee_id: UUID) -> Employee | None:
        result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
        return result.scalars().first()

    async def _get_workflow_tasks(self, workflow_id: UUID) -> list[OnboardingTask]:
        result = await self.db.execute(select(OnboardingTask).where(OnboardingTask.workflow_id == workflow_id))
        return list(result.scalars().all())

    def _build_graph_state(
        self,
        employee: Employee,
        workflow: OnboardingWorkflow,
        tasks: list[OnboardingTask],
        is_new_workflow: bool,
    ) -> dict[str, Any]:
        return {
            "employee_id": str(employee.id),
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "employee_email": employee.email,
            "manager_id": str(employee.manager_id) if employee.manager_id else None,
            "joining_date": employee.joining_date.isoformat(),
            "workflow_id": str(workflow.id),
            "current_state": workflow.current_state,
            "completion_percentage": workflow.completion_percentage,
            "is_new_workflow": is_new_workflow,
            "existing_tasks": [self._task_to_state(task) for task in tasks],
            "task_blueprints": [],
            "notifications": [],
            "events": [],
            "escalations": [],
            "errors": [],
        }

    def _task_to_state(self, task: OnboardingTask) -> dict[str, Any]:
        return {
            "id": str(task.id),
            "stage": self._infer_stage(task.title),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "assigned_to": str(task.assigned_to) if task.assigned_to else None,
        }

    async def _apply_task_blueprints(
        self,
        workflow_id: UUID,
        task_blueprints: list[dict[str, Any]],
    ) -> list[OnboardingTask]:
        existing_tasks = await self._get_workflow_tasks(workflow_id)
        existing_keys = {(self._infer_stage(task.title), task.title) for task in existing_tasks}
        created_tasks: list[OnboardingTask] = []

        for blueprint in task_blueprints:
            key = (blueprint["stage"], blueprint["title"])
            if key in existing_keys:
                continue

            task = OnboardingTask(
                workflow_id=workflow_id,
                title=blueprint["title"],
                description=blueprint.get("description"),
                status=blueprint.get("status", "pending"),
                priority=blueprint.get("priority", "medium"),
                due_date=self._parse_due_date(blueprint.get("due_date")),
                assigned_to=UUID(blueprint["assigned_to"]) if blueprint.get("assigned_to") else None,
            )
            self.db.add(task)
            created_tasks.append(task)
            existing_keys.add(key)

        await self.db.flush()
        return created_tasks

    async def _apply_workflow_state(
        self,
        employee: Employee,
        workflow: OnboardingWorkflow,
        result: dict[str, Any],
    ) -> None:
        workflow.current_state = result["current_state"]
        workflow.completion_percentage = result["completion_percentage"]
        workflow.completed_at = datetime.now(timezone.utc) if result["current_state"] == "completed" else None

        if result["current_state"] == "completed":
            employee.onboarding_status = "completed"
        else:
            employee.onboarding_status = "in_progress"

        await self.db.flush()

    async def _persist_events(
        self,
        employee_id: UUID,
        workflow_id: UUID,
        events: list[dict[str, Any]],
    ) -> None:
        for event in events:
            model = OnboardingOrchestrationEvent(
                workflow_id=workflow_id,
                employee_id=employee_id,
                event_type=event["event_type"],
                status=event.get("status", "success"),
                state_from=event.get("state_from"),
                state_to=event.get("state_to"),
                message=event["message"],
                payload=event.get("payload"),
            )
            self.db.add(model)
        await self.db.flush()

    async def _send_milestone_email(self, employee: Employee, new_state: str) -> None:
        """Fire a milestone email when the workflow enters a notable state."""
        _MILESTONE_LABELS: dict[str, str] = {
            "initiated": "Onboarding Started",
            "provisioning": "HR Review Completed",
            "meetings_scheduled": "IT Provisioning Completed",
            "documents_shared": "Documents Shared",
            "completed": "Onboarding Completed",
        }
        milestone = _MILESTONE_LABELS.get(new_state)
        if not milestone:
            return
        await self.notification_service.send_milestone_email(
            milestone=milestone,
            employee_email=employee.email,
            employee_name=f"{employee.first_name} {employee.last_name}",
            company_email=employee.company_email or f"{employee.first_name.lower()}.{employee.last_name.lower()}@amzur.com",
            department=employee.department,
            manager_id=employee.manager_id,
        )

    def _send_notifications(
        self,
        employee: Employee,
        notifications: list[dict[str, str]],
    ) -> None:
        if not notifications:
            return

        for notification in notifications:
            title = notification.get("title", "Onboarding Update")
            message = notification.get("message", "")
            self.notification_service.send_email_notification(employee.email, title, message)

    async def _resolve_notification_recipients(self, employee: Employee) -> list[UUID]:
        recipients = await self.notification_service.get_admin_recipient_ids()
        if employee.manager_id:
            manager_result = await self.db.execute(
                select(User.id).where(User.id == employee.manager_id)
            )
            manager_id = manager_result.scalars().first()
            if manager_id:
                recipients.append(manager_id)
        return list(dict.fromkeys(recipients))

    def _parse_due_date(self, value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    def _infer_stage(self, title: str) -> str:
        for stage, stage_tasks in DEFAULT_TASK_BLUEPRINTS.items():
            if any(task["title"] == title for task in stage_tasks):
                return stage
        return "hr_review"

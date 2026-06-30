"""
Onboarding service for workflow and task management.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Employee, OnboardingOrchestrationEvent, OnboardingTask, OnboardingWorkflow
from ..schemas import (
    OnboardingWorkflowCreate,
    OnboardingWorkflowUpdate,
    OnboardingTaskCreate,
    OnboardingTaskUpdate,
    OnboardingTaskResponse,
)
from .notification import NotificationService
from .orchestration import OrchestrationService
from .base import BaseService


class OnboardingService(BaseService):
    """Service for managing onboarding workflows and tasks."""

    async def _resolve_resume_state(self, workflow_id: UUID) -> str:
        """Resolve the last pre-pause state for a workflow."""
        paused_stmt = (
            select(OnboardingOrchestrationEvent)
            .where(
                OnboardingOrchestrationEvent.workflow_id == workflow_id,
                OnboardingOrchestrationEvent.event_type == "workflow_paused",
            )
            .order_by(OnboardingOrchestrationEvent.created_at.desc())
            .limit(1)
        )
        paused_result = await self.db.execute(paused_stmt)
        paused_event = paused_result.scalars().first()

        if not paused_event:
            return "hr_review"

        payload = paused_event.payload or {}
        payload_previous_state = payload.get("previous_state")
        if isinstance(payload_previous_state, str) and payload_previous_state:
            return payload_previous_state

        if paused_event.state_from:
            return paused_event.state_from

        return "hr_review"

    async def _apply_pause_action(
        self,
        workflow: OnboardingWorkflow,
        employee: Employee,
        note: str | None,
    ) -> tuple[str, str, str, str]:
        workflow.current_state = "paused"
        workflow.completed_at = None
        employee.onboarding_status = "paused"
        return "workflow_paused", "success", note or "Workflow paused by operator.", workflow.current_state

    async def _apply_resume_action(
        self,
        workflow: OnboardingWorkflow,
        employee: Employee,
        note: str | None,
    ) -> tuple[str, str, str, str]:
        if workflow.current_state == "paused":
            workflow.current_state = await self._resolve_resume_state(workflow.id)

        if workflow.current_state == "completed":
            employee.onboarding_status = "completed"
        else:
            employee.onboarding_status = "in_progress"

        return "workflow_resumed", "success", note or "Workflow resumed by operator.", workflow.current_state

    async def _apply_complete_action(
        self,
        workflow: OnboardingWorkflow,
        employee: Employee,
        now: datetime,
        note: str | None,
    ) -> tuple[str, str, str, str]:
        workflow.current_state = "completed"
        workflow.completion_percentage = 100
        workflow.completed_at = now
        employee.onboarding_status = "completed"
        return "workflow_completed", "success", note or "Workflow force-completed by operator.", workflow.current_state

    async def create_workflow(
        self, request: OnboardingWorkflowCreate
    ) -> OnboardingWorkflow:
        """
        Create a new onboarding workflow for an employee.

        Args:
            request: Workflow creation request

        Returns:
            Created workflow
        """
        existing_stmt = (
            select(OnboardingWorkflow)
            .where(OnboardingWorkflow.employee_id == request.employee_id)
            .order_by(OnboardingWorkflow.created_at.asc())
            .limit(1)
        )
        existing_result = await self.db.execute(existing_stmt)
        existing_workflow = existing_result.scalars().first()
        if existing_workflow:
            return existing_workflow

        workflow = OnboardingWorkflow(
            employee_id=request.employee_id,
            current_state=request.current_state,
            completion_percentage=request.completion_percentage,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow(self, workflow_id: UUID) -> OnboardingWorkflow | None:
        """
        Get a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow or None if not found
        """
        stmt = select(OnboardingWorkflow).where(
            OnboardingWorkflow.id == workflow_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_workflows(
        self, employee_id: UUID | None = None, skip: int = 0, limit: int = 10
    ) -> list[OnboardingWorkflow]:
        """
        List workflows with optional filtering.

        Args:
            employee_id: Filter by employee ID
            skip: Skip count for pagination
            limit: Limit for pagination

        Returns:
            List of workflows
        """
        stmt = select(OnboardingWorkflow)
        
        if employee_id:
            stmt = stmt.where(OnboardingWorkflow.employee_id == employee_id)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_workflow(
        self, workflow_id: UUID, request: OnboardingWorkflowUpdate
    ) -> OnboardingWorkflow | None:
        """
        Update a workflow.

        Args:
            workflow_id: Workflow ID
            request: Update request

        Returns:
            Updated workflow or None if not found
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)

        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def update_workflow_state(
        self, workflow_id: UUID, new_state: str
    ) -> OnboardingWorkflow | None:
        """
        Update workflow state and track completion.

        Args:
            workflow_id: Workflow ID
            new_state: New state value

        Returns:
            Updated workflow or None if not found
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        workflow.current_state = new_state

        # Update completion percentage based on tasks
        completion = await self.get_workflow_progress(workflow_id)
        workflow.completion_percentage = completion["completion_percentage"]

        # Mark as completed if all tasks are done
        if new_state == "completed":
            workflow.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow_progress(
        self, workflow_id: UUID
    ) -> dict:
        """
        Get workflow progress including task statistics.

        Args:
            workflow_id: Workflow ID

        Returns:
            Progress dictionary with completion percentage and task stats
        """
        # Get workflow
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return {
                "workflow_id": workflow_id,
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "in_progress_tasks": 0,
                "completion_percentage": 0,
                "current_state": "unknown",
            }

        # Count tasks by status
        stmt = select(OnboardingTask).where(
            OnboardingTask.workflow_id == workflow_id
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == "completed")
        pending_tasks = sum(1 for t in tasks if t.status == "pending")
        in_progress_tasks = sum(1 for t in tasks if t.status == "in_progress")

        completion_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        return {
            "workflow_id": workflow_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_percentage": int(completion_percentage),
            "current_state": workflow.current_state,
        }

    async def create_task(
        self, request: OnboardingTaskCreate
    ) -> OnboardingTask:
        """
        Create a new task in a workflow.

        Args:
            request: Task creation request

        Returns:
            Created task
        """
        task = OnboardingTask(**request.model_dump())
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        workflow = await self.get_workflow(task.workflow_id)
        if workflow:
            self.db.add(
                OnboardingOrchestrationEvent(
                    workflow_id=workflow.id,
                    employee_id=workflow.employee_id,
                    event_type="task_created",
                    status="success",
                    state_from=workflow.current_state,
                    state_to=workflow.current_state,
                    message=f"Task created: {task.title}",
                    payload={"task_id": str(task.id), "priority": task.priority},
                )
            )
            await self.db.flush()

        notification_service = NotificationService(self.db)
        await notification_service.create_task_assignment_notifications([task])

        orchestrator = OrchestrationService(self.db)
        await orchestrator.sync_workflow_state(task.workflow_id)
        return task

    async def get_task(self, task_id: UUID) -> OnboardingTask | None:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None if not found
        """
        stmt = select(OnboardingTask).where(OnboardingTask.id == task_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_workflow_tasks(
        self, workflow_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[OnboardingTask]:
        """
        Get all tasks for a workflow.

        Args:
            workflow_id: Workflow ID
            skip: Skip count for pagination
            limit: Limit for pagination

        Returns:
            List of tasks
        """
        stmt = (
            select(OnboardingTask)
            .where(OnboardingTask.workflow_id == workflow_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_task(
        self, task_id: UUID, request: OnboardingTaskUpdate
    ) -> OnboardingTask | None:
        """
        Update a task.

        Args:
            task_id: Task ID
            request: Update request

        Returns:
            Updated task or None if not found
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        was_completed = task.status == "completed"
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        # Mark completed_at when task is marked complete
        if request.status == "completed" and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(task)

        workflow = await self.get_workflow(task.workflow_id)
        if workflow:
            self.db.add(
                OnboardingOrchestrationEvent(
                    workflow_id=workflow.id,
                    employee_id=workflow.employee_id,
                    event_type="task_updated",
                    status="success",
                    state_from=workflow.current_state,
                    state_to=workflow.current_state,
                    message=f"Task updated: {task.title}",
                    payload={
                        "task_id": str(task.id),
                        "status": task.status,
                        "priority": task.priority,
                    },
                )
            )
            await self.db.flush()

        if task.status == "completed" and not was_completed:
            notification_service = NotificationService(self.db)
            await notification_service.create_task_completed_notification(task)

        orchestrator = OrchestrationService(self.db)
        await orchestrator.sync_workflow_state(task.workflow_id)
        return task

    async def apply_workflow_action(
        self,
        workflow_id: UUID,
        action: str,
        actor_user_id: UUID,
        note: str | None = None,
    ) -> tuple[OnboardingWorkflow | None, OnboardingOrchestrationEvent | None, str]:
        """Apply lifecycle action (pause/resume/escalate/complete) on a workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None, None, "Workflow not found"

        employee_stmt = select(Employee).where(Employee.id == workflow.employee_id)
        employee_result = await self.db.execute(employee_stmt)
        employee = employee_result.scalars().first()
        if not employee:
            return None, None, "Employee not found"

        now = datetime.now(timezone.utc)
        previous_state = workflow.current_state

        if action == "pause":
            event_type, event_status, message, state_to = await self._apply_pause_action(
                workflow,
                employee,
                note,
            )
        elif action == "resume":
            event_type, event_status, message, state_to = await self._apply_resume_action(
                workflow,
                employee,
                note,
            )
        elif action == "escalate":
            event_type = "escalation"
            event_status = "warning"
            message = note or "Workflow escalated for priority attention."
            state_to = workflow.current_state
        elif action == "complete":
            event_type, event_status, message, state_to = await self._apply_complete_action(
                workflow,
                employee,
                now,
                note,
            )
        else:
            return None, None, "Unsupported action"

        event = OnboardingOrchestrationEvent(
            workflow_id=workflow.id,
            employee_id=workflow.employee_id,
            event_type=event_type,
            status=event_status,
            state_from=previous_state,
            state_to=state_to,
            message=message,
            payload={
                "action": action,
                "actor_user_id": str(actor_user_id),
                "note": note,
                "previous_state": previous_state,
                "current_state": state_to,
            },
        )
        self.db.add(event)
        await self.db.flush()

        notification_service = NotificationService(self.db)
        recipients = await notification_service.get_admin_recipient_ids()
        if employee.manager_id:
            recipients.append(employee.manager_id)
        recipients.append(actor_user_id)
        recipients = list(dict.fromkeys(recipients))

        await notification_service.create_workflow_event_notifications(
            recipient_ids=recipients,
            employee_name=f"{employee.first_name} {employee.last_name}",
            workflow_id=workflow.id,
            events=[
                {
                    "event_type": event_type,
                    "state_from": previous_state,
                    "state_to": state_to,
                    "message": message,
                    "payload": {"action": action},
                }
            ],
            commit=False,
        )

        await self.db.commit()
        await self.db.refresh(workflow)
        await self.db.refresh(event)
        return workflow, event, message

    async def complete_task(self, task_id: UUID) -> OnboardingTask | None:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID

        Returns:
            Updated task or None if not found
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(task)

        notification_service = NotificationService(self.db)
        await notification_service.create_task_completed_notification(task)

        orchestrator = OrchestrationService(self.db)
        await orchestrator.sync_workflow_state(task.workflow_id)
        return task

    async def get_employee_onboarding_summary(
        self, employee_id: UUID
    ) -> dict:
        """
        Get complete onboarding summary for an employee.

        Args:
            employee_id: Employee ID

        Returns:
            Onboarding summary with workflow and task information
        """
        # Get employee
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await self.db.execute(stmt)
        employee = result.scalars().first()

        if not employee:
            return {
                "employee_id": employee_id,
                "found": False,
                "workflows": [],
                "total_progress": 0,
            }

        # Get workflows for employee
        workflows = await self.get_workflows(employee_id=employee_id)

        # Get progress for each workflow
        workflow_summaries = []
        for workflow in workflows:
            progress = await self.get_workflow_progress(workflow.id)
            workflow_summaries.append(
                {
                    "workflow_id": workflow.id,
                    "created_at": workflow.created_at,
                    **progress,
                }
            )

        # Calculate overall progress
        total_progress = (
            sum(w["completion_percentage"] for w in workflow_summaries)
            / len(workflow_summaries)
            if workflow_summaries
            else 0
        )

        return {
            "employee_id": employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "employee_email": employee.email,
            "found": True,
            "onboarding_status": employee.onboarding_status,
            "workflows": workflow_summaries,
            "total_progress": int(total_progress),
        }

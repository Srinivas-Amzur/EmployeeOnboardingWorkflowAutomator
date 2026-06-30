"""Audit service for cross-entity activity reporting."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from sqlalchemy import select

from ..models import Employee, Notification, OnboardingOrchestrationEvent, OnboardingTask, OnboardingWorkflow, User
from .base import BaseService


ACTION_EMPLOYEE_CREATED = "Employee Created"
ACTION_WORKFLOW_STARTED = "Workflow Started"
ACTION_WORKFLOW_UPDATED = "Workflow Updated"
ACTION_WORKFLOW_COMPLETED = "Workflow Completed"
ACTION_TASK_CREATED = "Task Created"
ACTION_TASK_UPDATED = "Task Updated"
ACTION_NOTIFICATION_GENERATED = "Notification Generated"
ACTION_DOCUMENT_UPLOADED = "Document Uploaded"
ACTION_AI_QUERY_EXECUTED = "AI Query Executed"


class AuditService(BaseService):
    """Builds normalized audit entries from existing persisted entities."""

    async def list_logs(
        self,
        viewer_user_id: str,
        viewer_email: str,
        viewer_role: str,
        skip: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        normalized_role = (viewer_role or "").lower()
        viewer_uuid = self._safe_uuid(viewer_user_id)

        # Parallelise all independent data-fetch calls
        (
            users,
            viewer_employee_id,
            managed_employee_ids_list,
            workflow_employee_map,
            task_workflow_map,
            employees,
            workflows,
            tasks,
            orchestration_events,
            notifications,
        ) = await asyncio.gather(
            self._get_users_map(),
            self._resolve_employee_id_by_email(viewer_email),
            self._resolve_managed_employee_ids(viewer_uuid) if viewer_uuid else asyncio.sleep(0, result=set()),
            self._get_workflow_employee_map(),
            self._get_task_workflow_map(),
            self._get_recent_employees(limit=250),
            self._get_recent_workflows(limit=250),
            self._get_recent_tasks(limit=350),
            self._get_recent_orchestration_events(limit=500),
            self._get_recent_notifications(limit=500),
        )
        managed_employee_ids: set[UUID] = managed_employee_ids_list  # type: ignore[assignment]

        entries: list[dict[str, Any]] = []
        entries.extend(self._build_employee_entries_sync(employees))
        entries.extend(self._build_workflow_entries_sync(workflows))
        entries.extend(self._build_task_entries_sync(tasks, workflow_employee_map))
        entries.extend(self._build_orchestration_entries_sync(orchestration_events))
        entries.extend(self._build_notification_entries_sync(notifications, users, workflow_employee_map))

        filtered = self._filter_entries_by_role(
            entries=entries,
            role=normalized_role,
            viewer_user_id=viewer_uuid,
            viewer_employee_id=viewer_employee_id,
            managed_employee_ids=managed_employee_ids,
            workflow_employee_map=workflow_employee_map,
            task_workflow_map=task_workflow_map,
        )

        filtered.sort(key=lambda item: item["timestamp"], reverse=True)
        total = len(filtered)
        paged = filtered[skip : skip + limit]
        return {"items": [self._sanitize_entry(item) for item in paged], "total": total}

    # ── Sync builders (called after parallel data fetch) ──────────────────────

    def _build_employee_entries_sync(self, employees: list[Employee]) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for employee in employees:
            entries.append(
                {
                    "timestamp": employee.created_at,
                    "user": "System",
                    "action": ACTION_EMPLOYEE_CREATED,
                    "entity": "employee",
                    "entity_id": str(employee.id),
                    "details": (
                        f"{employee.first_name} {employee.last_name} ({employee.email}) "
                        f"joined {employee.department} as {employee.designation}."
                    ),
                    "employee_id": employee.id,
                }
            )
        return entries

    def _build_workflow_entries_sync(self, workflows: list[OnboardingWorkflow]) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for workflow in workflows:
            entries.append(
                {
                    "timestamp": workflow.started_at,
                    "user": "System",
                    "action": ACTION_WORKFLOW_STARTED,
                    "entity": "workflow",
                    "entity_id": str(workflow.id),
                    "details": f"Workflow initiated in state '{workflow.current_state}'.",
                    "workflow_id": workflow.id,
                    "employee_id": workflow.employee_id,
                }
            )

            if workflow.updated_at > workflow.created_at and workflow.current_state != "completed":
                entries.append(
                    {
                        "timestamp": workflow.updated_at,
                        "user": "System",
                        "action": ACTION_WORKFLOW_UPDATED,
                        "entity": "workflow",
                        "entity_id": str(workflow.id),
                        "details": f"Workflow updated; current state is '{workflow.current_state}'.",
                        "workflow_id": workflow.id,
                        "employee_id": workflow.employee_id,
                    }
                )

            if workflow.completed_at:
                entries.append(
                    {
                        "timestamp": workflow.completed_at,
                        "user": "System",
                        "action": ACTION_WORKFLOW_COMPLETED,
                        "entity": "workflow",
                        "entity_id": str(workflow.id),
                        "details": "Workflow marked as completed.",
                        "workflow_id": workflow.id,
                        "employee_id": workflow.employee_id,
                    }
                )
        return entries

    def _build_task_entries_sync(self, tasks: list[OnboardingTask], workflow_employee_map: dict[UUID, UUID]) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for task in tasks:
            entries.append(
                {
                    "timestamp": task.created_at,
                    "user": "System",
                    "action": ACTION_TASK_CREATED,
                    "entity": "task",
                    "entity_id": str(task.id),
                    "details": f"Task '{task.title}' created with priority '{task.priority}'.",
                    "task_id": task.id,
                    "workflow_id": task.workflow_id,
                    "employee_id": workflow_employee_map.get(task.workflow_id),
                    "assigned_to": task.assigned_to,
                }
            )
            if task.updated_at > task.created_at:
                entries.append(
                    {
                        "timestamp": task.updated_at,
                        "user": "System",
                        "action": ACTION_TASK_UPDATED,
                        "entity": "task",
                        "entity_id": str(task.id),
                        "details": f"Task '{task.title}' updated; status is '{task.status}'.",
                        "task_id": task.id,
                        "workflow_id": task.workflow_id,
                        "employee_id": workflow_employee_map.get(task.workflow_id),
                        "assigned_to": task.assigned_to,
                    }
                )
        return entries

    def _build_orchestration_entries_sync(self, orchestration_events: list[OnboardingOrchestrationEvent]) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for event in orchestration_events:
            action = self._resolve_orchestration_action(event.event_type)
            if not action:
                continue

            entries.append(
                {
                    "timestamp": event.created_at,
                    "user": "System",
                    "action": action,
                    "entity": "workflow",
                    "entity_id": str(event.workflow_id),
                    "details": event.message,
                    "workflow_id": event.workflow_id,
                    "employee_id": event.employee_id,
                    "actor_user_id": self._extract_actor_user_id(event.payload),
                }
            )
        return entries

    def _build_notification_entries_sync(
        self,
        notifications: list[Notification],
        users: dict[UUID, str],
        workflow_employee_map: dict[UUID, UUID],
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for note in notifications:
            recipient = users.get(note.user_id, "Unknown User")
            action = self._resolve_notification_action(note)
            entries.append(
                {
                    "timestamp": note.created_at,
                    "user": recipient,
                    "action": action,
                    "entity": "notification",
                    "entity_id": str(note.id),
                    "details": f"{note.title}: {note.message}",
                    "notification_id": note.id,
                    "notification_type": note.notification_type,
                    "user_id": note.user_id,
                    "workflow_id": self._extract_workflow_id(note.payload),
                    "employee_id": self._resolve_employee_id_from_workflow_payload(note.payload, workflow_employee_map),
                    "actor_user_id": self._extract_actor_user_id(note.payload),
                }
            )
        return entries

    def _resolve_notification_action(self, note: Notification) -> str:
        if note.notification_type == "ai_indexing_completed":
            return ACTION_DOCUMENT_UPLOADED
        if note.notification_type == "ai_orchestration" and (note.payload or {}).get("audit_action") == "ai_query_executed":
            return ACTION_AI_QUERY_EXECUTED
        return ACTION_NOTIFICATION_GENERATED

    def _filter_entries_by_role(
        self,
        entries: list[dict[str, Any]],
        role: str,
        viewer_user_id: UUID | None,
        viewer_employee_id: UUID | None,
        managed_employee_ids: set[UUID],
        workflow_employee_map: dict[UUID, UUID],
        task_workflow_map: dict[UUID, UUID],
    ) -> list[dict[str, Any]]:
        if role in {"admin", "hr_admin"}:
            return entries

        if role in {"it_admin", "it-admin", "it"}:
            allowed_entities = {"workflow", "task", "notification"}
            allowed_actions = {
                ACTION_WORKFLOW_STARTED,
                ACTION_WORKFLOW_UPDATED,
                ACTION_WORKFLOW_COMPLETED,
                ACTION_TASK_CREATED,
                ACTION_TASK_UPDATED,
                ACTION_NOTIFICATION_GENERATED,
                ACTION_DOCUMENT_UPLOADED,
                ACTION_AI_QUERY_EXECUTED,
            }
            return [
                entry for entry in entries
                if entry.get("entity") in allowed_entities and entry.get("action") in allowed_actions
            ]

        if role == "manager":
            if not managed_employee_ids and not viewer_user_id:
                return []
            return [
                entry
                for entry in entries
                if self._is_manager_visible(
                    entry=entry,
                    managed_employee_ids=managed_employee_ids,
                    viewer_user_id=viewer_user_id,
                    workflow_employee_map=workflow_employee_map,
                    task_workflow_map=task_workflow_map,
                )
            ]

        return [
            entry
            for entry in entries
            if self._is_employee_visible(
                entry=entry,
                viewer_user_id=viewer_user_id,
                viewer_employee_id=viewer_employee_id,
                workflow_employee_map=workflow_employee_map,
                task_workflow_map=task_workflow_map,
            )
        ]

    def _is_manager_visible(
        self,
        entry: dict[str, Any],
        managed_employee_ids: set[UUID],
        viewer_user_id: UUID | None,
        workflow_employee_map: dict[UUID, UUID],
        task_workflow_map: dict[UUID, UUID],
    ) -> bool:
        employee_id = self._resolve_employee_id_from_entry(entry, workflow_employee_map, task_workflow_map)
        if employee_id and employee_id in managed_employee_ids:
            return True

        entry_user_id = entry.get("user_id")
        if viewer_user_id and entry_user_id and entry_user_id == viewer_user_id:
            return True

        actor_user_id = entry.get("actor_user_id")
        if viewer_user_id and actor_user_id and actor_user_id == viewer_user_id:
            return True

        return False

    def _is_employee_visible(
        self,
        entry: dict[str, Any],
        viewer_user_id: UUID | None,
        viewer_employee_id: UUID | None,
        workflow_employee_map: dict[UUID, UUID],
        task_workflow_map: dict[UUID, UUID],
    ) -> bool:
        employee_id = self._resolve_employee_id_from_entry(entry, workflow_employee_map, task_workflow_map)
        if viewer_employee_id and employee_id and employee_id == viewer_employee_id:
            return True

        entry_user_id = entry.get("user_id")
        if viewer_user_id and entry_user_id and entry_user_id == viewer_user_id:
            return True

        actor_user_id = entry.get("actor_user_id")
        if viewer_user_id and actor_user_id and actor_user_id == viewer_user_id:
            return True

        assigned_to = entry.get("assigned_to")
        if viewer_user_id and assigned_to and assigned_to == viewer_user_id:
            return True

        return False

    def _resolve_employee_id_from_entry(
        self,
        entry: dict[str, Any],
        workflow_employee_map: dict[UUID, UUID],
        task_workflow_map: dict[UUID, UUID],
    ) -> UUID | None:
        employee_id = entry.get("employee_id")
        if employee_id:
            return employee_id

        workflow_id = entry.get("workflow_id")
        if workflow_id and workflow_id in workflow_employee_map:
            return workflow_employee_map[workflow_id]

        task_id = entry.get("task_id")
        if task_id and task_id in task_workflow_map:
            workflow_for_task = task_workflow_map[task_id]
            return workflow_employee_map.get(workflow_for_task)

        return None

    async def _resolve_employee_id_by_email(self, email: str) -> UUID | None:
        if not email:
            return None
        result = await self.db.execute(select(Employee.id).where(Employee.email == email))
        return result.scalars().first()

    async def _resolve_managed_employee_ids(self, manager_user_id: UUID) -> set[UUID]:
        result = await self.db.execute(select(Employee.id).where(Employee.manager_id == manager_user_id))
        return set(result.scalars().all())

    async def _get_workflow_employee_map(self) -> dict[UUID, UUID]:
        result = await self.db.execute(select(OnboardingWorkflow.id, OnboardingWorkflow.employee_id))
        return {row[0]: row[1] for row in result.all()}

    async def _get_task_workflow_map(self) -> dict[UUID, UUID]:
        result = await self.db.execute(select(OnboardingTask.id, OnboardingTask.workflow_id))
        return {row[0]: row[1] for row in result.all()}

    def _sanitize_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "timestamp": entry["timestamp"],
            "user": entry["user"],
            "action": entry["action"],
            "entity": entry["entity"],
            "entity_id": entry["entity_id"],
            "details": entry["details"],
        }

    def _extract_actor_user_id(self, payload: dict[str, Any] | None) -> UUID | None:
        if not payload:
            return None
        return self._safe_uuid(payload.get("actor_user_id"))

    def _extract_workflow_id(self, payload: dict[str, Any] | None) -> UUID | None:
        if not payload:
            return None
        return self._safe_uuid(payload.get("workflow_id"))

    def _resolve_employee_id_from_workflow_payload(
        self,
        payload: dict[str, Any] | None,
        workflow_employee_map: dict[UUID, UUID],
    ) -> UUID | None:
        workflow_id = self._extract_workflow_id(payload)
        if not workflow_id:
            return None
        return workflow_employee_map.get(workflow_id)

    def _safe_uuid(self, value: Any) -> UUID | None:
        try:
            return UUID(str(value)) if value else None
        except (ValueError, TypeError):
            return None

    async def _get_users_map(self) -> dict[UUID, str]:
        result = await self.db.execute(select(User.id, User.name, User.email))
        rows = result.all()
        return {row[0]: (row[1] or row[2]) for row in rows}

    async def _get_recent_employees(self, limit: int) -> list[Employee]:
        result = await self.db.execute(select(Employee).order_by(Employee.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def _get_recent_workflows(self, limit: int) -> list[OnboardingWorkflow]:
        result = await self.db.execute(select(OnboardingWorkflow).order_by(OnboardingWorkflow.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def _get_recent_tasks(self, limit: int) -> list[OnboardingTask]:
        result = await self.db.execute(select(OnboardingTask).order_by(OnboardingTask.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def _get_recent_orchestration_events(self, limit: int) -> list[OnboardingOrchestrationEvent]:
        result = await self.db.execute(
            select(OnboardingOrchestrationEvent)
            .order_by(OnboardingOrchestrationEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_recent_notifications(self, limit: int) -> list[Notification]:
        result = await self.db.execute(select(Notification).order_by(Notification.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    def _resolve_orchestration_action(self, event_type: str) -> str | None:
        mapping = {
            "workflow_started": ACTION_WORKFLOW_STARTED,
            "workflow_state_changed": ACTION_WORKFLOW_UPDATED,
            "workflow_completed": ACTION_WORKFLOW_COMPLETED,
            "task_created": ACTION_TASK_CREATED,
            "task_updated": ACTION_TASK_UPDATED,
            "escalation": ACTION_WORKFLOW_UPDATED,
            "workflow_paused": ACTION_WORKFLOW_UPDATED,
            "workflow_resumed": ACTION_WORKFLOW_UPDATED,
        }
        return mapping.get(event_type)
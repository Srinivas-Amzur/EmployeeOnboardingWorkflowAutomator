"""
Analytics service for dashboard statistics.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Employee,
    Notification,
    OnboardingMeeting,
    OnboardingOrchestrationEvent,
    OnboardingTask,
    OnboardingWorkflow,
)
from .base import BaseService
from .audit import AuditService


class AnalyticsService(BaseService):
    """Service for computing dashboard and workflow analytics."""

    async def get_dashboard_stats(self) -> dict:
        """Compute aggregated statistics for the main dashboard."""
        # Sequential queries — AsyncSession is not safe for concurrent asyncio.gather
        wf_result = await self.db.execute(
            select(
                OnboardingWorkflow.current_state,
                func.count(OnboardingWorkflow.id).label("cnt"),
            ).group_by(OnboardingWorkflow.current_state)
        )
        avg_result = await self.db.execute(
            select(func.avg(OnboardingWorkflow.completion_percentage))
        )
        task_result = await self.db.execute(
            select(
                OnboardingTask.status,
                func.count(OnboardingTask.id).label("cnt"),
            ).group_by(OnboardingTask.status)
        )
        emp_result = await self.db.execute(
            select(
                Employee.onboarding_status,
                func.count(Employee.id).label("cnt"),
            ).group_by(Employee.onboarding_status)
        )
        delayed_wf_result = await self.db.execute(
            select(
                func.count(func.distinct(OnboardingOrchestrationEvent.workflow_id))
            ).where(OnboardingOrchestrationEvent.event_type == "escalation")
        )
        avg_days_result = await self.db.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        OnboardingWorkflow.completed_at - OnboardingWorkflow.started_at,
                    )
                    / 86400.0
                )
            ).where(OnboardingWorkflow.completed_at.is_not(None))
        )
        docs_result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.notification_type == "ai_indexing_completed"
            )
        )
        meeting_result = await self.db.execute(
            select(
                OnboardingMeeting.status,
                func.count(OnboardingMeeting.id).label("cnt"),
            ).group_by(OnboardingMeeting.status)
        )
        ai_usage_result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.notification_type == "ai_orchestration"
            )
        )
        recent_activity_result = await self.db.execute(
            select(Notification).order_by(Notification.created_at.desc()).limit(8)
        )

        # ── Unpack results ────────────────────────────────────────────────
        workflows_by_state: dict[str, int] = {row[0]: row[1] for row in wf_result.all()}
        total_workflows     = sum(workflows_by_state.values())
        completed_workflows = workflows_by_state.get("completed", 0)
        active_workflows    = total_workflows - completed_workflows
        average_completion  = int(avg_result.scalar() or 0)

        tasks_by_status: dict[str, int] = {row[0]: row[1] for row in task_result.all()}
        pending_tasks     = tasks_by_status.get("pending", 0)
        in_progress_tasks = tasks_by_status.get("in_progress", 0)
        completed_tasks   = tasks_by_status.get("completed", 0)

        employees_by_status: dict[str, int] = {row[0]: row[1] for row in emp_result.all()}
        total_employees = sum(employees_by_status.values())

        delayed_workflows             = int(delayed_wf_result.scalar() or 0)
        average_completion_time_days  = round(float(avg_days_result.scalar() or 0), 2)
        documents_uploaded            = int(docs_result.scalar() or 0)
        meetings_by_status            = {row[0]: row[1] for row in meeting_result.all()}
        ai_assistant_usage            = int(ai_usage_result.scalar() or 0)

        recent_activity = [
            {
                "id":        str(item.id),
                "timestamp": item.created_at.isoformat(),
                "type":      item.notification_type,
                "title":     item.title,
                "message":   item.message,
            }
            for item in recent_activity_result.scalars().all()
        ]

        return {
            "total_workflows":              total_workflows,
            "active_workflows":             active_workflows,
            "completed_workflows":          completed_workflows,
            "delayed_workflows":            delayed_workflows,
            "pending_tasks":                pending_tasks,
            "in_progress_tasks":            in_progress_tasks,
            "completed_tasks":              completed_tasks,
            "average_completion":           average_completion,
            "average_completion_time_days": average_completion_time_days,
            "workflows_by_state":           workflows_by_state,
            "total_employees":              total_employees,
            "employees_by_status":          employees_by_status,
            "documents_uploaded":           documents_uploaded,
            "ai_assistant_usage":           ai_assistant_usage,
            "meetings_total":               sum(meetings_by_status.values()),
            "meetings_by_status":           meetings_by_status,
            "upcoming_meetings":            meetings_by_status.get("scheduled", 0),
            "recent_activity":              recent_activity,
        }

    async def get_report_dataset(
        self,
        report_type: str,
        viewer_user_id,
        viewer_email: str,
        viewer_role: str,
    ) -> dict:
        """Build structured analytics export payload by report type."""
        normalized = report_type.lower()
        if normalized == "workflow":
            return await self._workflow_report_dataset()
        if normalized == "employee":
            return await self._employee_report_dataset()
        if normalized == "audit":
            return await self._audit_report_dataset(viewer_user_id, viewer_email, viewer_role)
        raise ValueError("Unsupported report type")

    async def _workflow_report_dataset(self) -> dict:
        stats = await self.get_dashboard_stats()

        rows_result = await self.db.execute(
            select(OnboardingWorkflow)
            .order_by(OnboardingWorkflow.created_at.desc())
            .limit(200)
        )
        workflows = rows_result.scalars().all()

        rows = [
            {
                "workflow_id": str(item.id),
                "employee_id": str(item.employee_id),
                "state": item.current_state,
                "completion_percentage": item.completion_percentage,
                "started_at": item.started_at.isoformat() if item.started_at else "",
                "completed_at": item.completed_at.isoformat() if item.completed_at else "",
                "created_at": item.created_at.isoformat(),
            }
            for item in workflows
        ]

        return {
            "title": "Workflow Report",
            "summary": {
                "total_workflows": stats["total_workflows"],
                "active_workflows": stats["active_workflows"],
                "completed_workflows": stats["completed_workflows"],
                "average_completion": stats["average_completion"],
                "delayed_workflows": stats["delayed_workflows"],
            },
            "rows": rows,
        }

    async def _employee_report_dataset(self) -> dict:
        stats = await self.get_dashboard_stats()
        rows_result = await self.db.execute(
            select(Employee)
            .order_by(Employee.created_at.desc())
            .limit(200)
        )
        employees = rows_result.scalars().all()

        rows = [
            {
                "employee_id": str(item.id),
                "name": f"{item.first_name} {item.last_name}",
                "email": item.email,
                "department": item.department,
                "designation": item.designation,
                "onboarding_status": item.onboarding_status,
                "joining_date": item.joining_date.isoformat(),
                "created_at": item.created_at.isoformat(),
            }
            for item in employees
        ]

        return {
            "title": "Employee Onboarding Report",
            "summary": {
                "total_employees": stats["total_employees"],
                "employees_by_status": stats["employees_by_status"],
                "meetings_total": stats["meetings_total"],
                "upcoming_meetings": stats["upcoming_meetings"],
            },
            "rows": rows,
        }

    async def _audit_report_dataset(self, viewer_user_id, viewer_email: str, viewer_role: str) -> dict:
        audit_service = AuditService(self.db)
        logs = await audit_service.list_logs(
            viewer_user_id=viewer_user_id,
            viewer_email=viewer_email,
            viewer_role=viewer_role,
            limit=300,
        )

        by_action: dict[str, int] = {}
        by_entity: dict[str, int] = {}
        rows = []
        for item in logs.items:
            by_action[item.action] = by_action.get(item.action, 0) + 1
            by_entity[item.entity_type] = by_entity.get(item.entity_type, 0) + 1
            rows.append(
                {
                    "timestamp": item.timestamp.isoformat(),
                    "action": item.action,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "actor_user_id": item.actor_user_id,
                    "details": str(item.details),
                }
            )

        return {
            "title": "Audit Activity Report",
            "summary": {
                "total_entries": logs.total,
                "actions": by_action,
                "entities": by_entity,
            },
            "rows": rows,
        }

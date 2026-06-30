"""Meeting service for onboarding calendar scheduling MVP."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from ..models import Employee, OnboardingMeeting, OnboardingOrchestrationEvent, OnboardingWorkflow
from ..schemas.meeting import MeetingCreate, MeetingUpdate
from .base import BaseService
from .notification import NotificationService


class MeetingService(BaseService):
    """Service for meeting persistence, scheduling, and workflow integration."""

    async def create_meeting(self, request: MeetingCreate, actor_user_id: UUID | None = None) -> OnboardingMeeting:
        """Create one meeting and emit onboarding side effects."""
        meeting = OnboardingMeeting(
            employee_id=request.employee_id,
            workflow_id=request.workflow_id,
            created_by=actor_user_id,
            meeting_type=request.meeting_type,
            title=request.title,
            description=request.description,
            scheduled_for=request.scheduled_for,
            duration_minutes=request.duration_minutes,
            location=request.location,
            meeting_url=request.meeting_url,
            status=request.status,
        )
        self.db.add(meeting)
        await self.db.flush()

        await self._integrate_with_workflow(
            employee_id=request.employee_id,
            workflow_id=request.workflow_id,
            event_type="meeting_scheduled",
            message=f"Meeting scheduled: {request.title}",
            actor_user_id=actor_user_id,
            note=None,
        )

        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting

    async def get_meeting(self, meeting_id: UUID) -> OnboardingMeeting | None:
        stmt = select(OnboardingMeeting).where(OnboardingMeeting.id == meeting_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_meetings(
        self,
        employee_id: UUID | None = None,
        workflow_id: UUID | None = None,
        upcoming_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[OnboardingMeeting]:
        stmt = select(OnboardingMeeting)

        if employee_id:
            stmt = stmt.where(OnboardingMeeting.employee_id == employee_id)

        if workflow_id:
            stmt = stmt.where(OnboardingMeeting.workflow_id == workflow_id)

        if upcoming_only:
            now = datetime.now(timezone.utc)
            stmt = stmt.where(
                OnboardingMeeting.scheduled_for >= now,
                OnboardingMeeting.status == "scheduled",
            )

        stmt = stmt.order_by(OnboardingMeeting.scheduled_for.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_meeting(
        self,
        meeting_id: UUID,
        request: MeetingUpdate,
        actor_user_id: UUID | None = None,
    ) -> OnboardingMeeting | None:
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(meeting, field, value)

        await self._integrate_with_workflow(
            employee_id=meeting.employee_id,
            workflow_id=meeting.workflow_id,
            event_type="meeting_updated",
            message=f"Meeting updated: {meeting.title}",
            actor_user_id=actor_user_id,
            note=None,
        )

        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting

    async def delete_meeting(self, meeting_id: UUID, actor_user_id: UUID | None = None) -> bool:
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return False

        employee_id = meeting.employee_id
        workflow_id = meeting.workflow_id
        title = meeting.title

        await self.db.delete(meeting)

        await self._integrate_with_workflow(
            employee_id=employee_id,
            workflow_id=workflow_id,
            event_type="meeting_cancelled",
            message=f"Meeting cancelled: {title}",
            actor_user_id=actor_user_id,
            note=None,
        )

        await self.db.commit()
        return True

    async def schedule_orientation_meeting(
        self,
        workflow_id: UUID,
        actor_user_id: UUID,
        scheduled_for: datetime | None,
        duration_minutes: int,
        location: str | None,
        meeting_url: str | None,
        note: str | None,
    ) -> OnboardingMeeting:
        return await self._schedule_single_workflow_meeting(
            workflow_id=workflow_id,
            actor_user_id=actor_user_id,
            meeting_type="orientation",
            default_title="Orientation Meeting",
            default_description="Formal orientation session for onboarding kickoff.",
            default_scheduled_for=scheduled_for,
            fallback_time_offset_days=0,
            duration_minutes=duration_minutes,
            location=location,
            meeting_url=meeting_url,
            note=note,
        )

    async def schedule_manager_introduction(
        self,
        workflow_id: UUID,
        actor_user_id: UUID,
        scheduled_for: datetime | None,
        duration_minutes: int,
        location: str | None,
        meeting_url: str | None,
        note: str | None,
    ) -> OnboardingMeeting:
        return await self._schedule_single_workflow_meeting(
            workflow_id=workflow_id,
            actor_user_id=actor_user_id,
            meeting_type="manager_introduction",
            default_title="Manager Introduction",
            default_description="Introductory session between employee and direct manager.",
            default_scheduled_for=scheduled_for,
            fallback_time_offset_days=0,
            duration_minutes=duration_minutes,
            location=location,
            meeting_url=meeting_url,
            note=note,
        )

    async def schedule_team_onboarding_session(
        self,
        workflow_id: UUID,
        actor_user_id: UUID,
        scheduled_for: datetime | None,
        duration_minutes: int,
        location: str | None,
        meeting_url: str | None,
        note: str | None,
    ) -> OnboardingMeeting:
        return await self._schedule_single_workflow_meeting(
            workflow_id=workflow_id,
            actor_user_id=actor_user_id,
            meeting_type="team_onboarding",
            default_title="Team Onboarding Session",
            default_description="First team onboarding and collaboration session.",
            default_scheduled_for=scheduled_for,
            fallback_time_offset_days=1,
            duration_minutes=duration_minutes,
            location=location,
            meeting_url=meeting_url,
            note=note,
        )

    async def _schedule_single_workflow_meeting(
        self,
        workflow_id: UUID,
        actor_user_id: UUID,
        meeting_type: str,
        default_title: str,
        default_description: str,
        default_scheduled_for: datetime | None,
        fallback_time_offset_days: int,
        duration_minutes: int,
        location: str | None,
        meeting_url: str | None,
        note: str | None,
    ) -> OnboardingMeeting:
        workflow, employee = await self._resolve_workflow_and_employee(workflow_id)

        meeting_time = default_scheduled_for or self._default_meeting_datetime(employee, fallback_time_offset_days)

        meeting = OnboardingMeeting(
            employee_id=employee.id,
            workflow_id=workflow.id,
            created_by=actor_user_id,
            meeting_type=meeting_type,
            title=default_title,
            description=default_description,
            scheduled_for=meeting_time,
            duration_minutes=duration_minutes,
            location=location,
            meeting_url=meeting_url,
            status="scheduled",
        )
        self.db.add(meeting)
        await self.db.flush()

        await self._integrate_with_workflow(
            employee_id=employee.id,
            workflow_id=workflow.id,
            event_type="meeting_scheduled",
            message=f"{default_title} scheduled.",
            actor_user_id=actor_user_id,
            note=note,
        )

        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting

    async def _resolve_workflow_and_employee(self, workflow_id: UUID) -> tuple[OnboardingWorkflow, Employee]:
        workflow_stmt = select(OnboardingWorkflow).where(OnboardingWorkflow.id == workflow_id)
        workflow_result = await self.db.execute(workflow_stmt)
        workflow = workflow_result.scalars().first()
        if not workflow:
            raise ValueError("Workflow not found")

        employee_stmt = select(Employee).where(Employee.id == workflow.employee_id)
        employee_result = await self.db.execute(employee_stmt)
        employee = employee_result.scalars().first()
        if not employee:
            raise ValueError("Employee not found")

        return workflow, employee

    def _default_meeting_datetime(self, employee: Employee, offset_days: int) -> datetime:
        joining_datetime = datetime.combine(employee.joining_date, time(hour=10, minute=0, tzinfo=timezone.utc))
        proposed = joining_datetime + timedelta(days=offset_days)

        now = datetime.now(timezone.utc)
        if proposed <= now:
            return now + timedelta(hours=2)
        return proposed

    async def _integrate_with_workflow(
        self,
        employee_id: UUID,
        workflow_id: UUID,
        event_type: str,
        message: str,
        actor_user_id: UUID | None,
        note: str | None,
    ) -> None:
        workflow_stmt = select(OnboardingWorkflow).where(OnboardingWorkflow.id == workflow_id)
        workflow_result = await self.db.execute(workflow_stmt)
        workflow = workflow_result.scalars().first()
        if not workflow:
            return

        employee_stmt = select(Employee).where(Employee.id == employee_id)
        employee_result = await self.db.execute(employee_stmt)
        employee = employee_result.scalars().first()
        if not employee:
            return

        previous_state = workflow.current_state
        if workflow.current_state not in {"completed", "paused"}:
            workflow.current_state = "meetings_scheduled"
            if employee.onboarding_status != "completed":
                employee.onboarding_status = "in_progress"

        event = OnboardingOrchestrationEvent(
            workflow_id=workflow.id,
            employee_id=employee.id,
            event_type=event_type,
            status="success",
            state_from=previous_state,
            state_to=workflow.current_state,
            message=message,
            payload={
                "actor_user_id": str(actor_user_id) if actor_user_id else None,
                "note": note,
            },
        )
        self.db.add(event)
        await self.db.flush()

        notification_service = NotificationService(self.db)
        recipients = await notification_service.get_admin_recipient_ids()
        if employee.manager_id:
            recipients.append(employee.manager_id)
        if actor_user_id:
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
                    "state_to": workflow.current_state,
                    "message": message,
                    "payload": {"note": note},
                }
            ],
            commit=False,
        )

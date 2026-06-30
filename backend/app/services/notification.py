"""Notification service for in-app notification center."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, select, update

from ..models import Notification, OnboardingTask, User
from ..schemas.notification import NotificationType
from .base import BaseService
from .email_service import EmailService


class NotificationService(BaseService):
    """Service for notification persistence and delivery."""

    def __init__(self, db):
        super().__init__(db)
        self.email_service = EmailService()

    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        payload: dict | None = None,
        commit: bool = True,
    ) -> Notification:
        """Create one in-app notification."""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type.value,
            title=title,
            message=message,
            payload=payload,
            is_read=False,
            read_at=None,
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        self.logger.info(
            "in_app_notification_created",
            extra={
                "notification_id": str(notification.id),
                "user_id": str(user_id),
                "notification_type": notification_type.value,
            },
        )
        if commit:
            await self.db.commit()
        return notification

    async def create_bulk_notifications(
        self,
        user_ids: list[UUID],
        notification_type: NotificationType,
        title: str,
        message: str,
        payload: dict | None = None,
        commit: bool = True,
    ) -> int:
        """Create the same notification for many users."""
        unique_user_ids = list(dict.fromkeys(user_ids))
        for user_id in unique_user_ids:
            self.db.add(
                Notification(
                    user_id=user_id,
                    notification_type=notification_type.value,
                    title=title,
                    message=message,
                    payload=payload,
                    is_read=False,
                    read_at=None,
                )
            )
        await self.db.flush()
        if commit:
            await self.db.commit()
        return len(unique_user_ids)

    async def list_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 30,
        unread_only: bool = False,
    ) -> list[Notification]:
        """List notifications for one user, newest first."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        """Return unread notification count for a user."""
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                and_(Notification.user_id == user_id, Notification.is_read.is_(False))
            )
        )
        return int(result.scalar() or 0)

    async def mark_as_read(
        self,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification | None:
        """Mark one notification as read if it belongs to user."""
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.id == notification_id, Notification.user_id == user_id)
            )
        )
        notification = result.scalars().first()
        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all unread notifications as read for one user."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read.is_(False)))
            .values(is_read=True, read_at=now, updated_at=now)
        )
        await self.db.commit()
        return int(result.rowcount or 0)

    async def get_admin_recipient_ids(self) -> list[UUID]:
        """Resolve active admin recipients for platform-level notifications."""
        result = await self.db.execute(
            select(User.id).where(
                and_(User.is_active.is_(True), User.role.in_(["admin", "hr_admin"]))
            )
        )
        return [row[0] for row in result.all()]

    async def create_task_assignment_notifications(
        self,
        tasks: list[OnboardingTask],
        commit: bool = True,
    ) -> int:
        """Create notifications for newly assigned tasks."""
        count = 0
        for task in tasks:
            if not task.assigned_to:
                continue
            await self.create_notification(
                user_id=task.assigned_to,
                notification_type=NotificationType.TASK_ASSIGNED,
                title="Task assigned",
                message=f"You were assigned: {task.title}",
                payload={"task_id": str(task.id), "workflow_id": str(task.workflow_id)},
                commit=False,
            )
            count += 1

        if commit and count:
            await self.db.commit()
        return count

    async def create_task_completed_notification(
        self,
        task: OnboardingTask,
        commit: bool = True,
    ) -> int:
        """Create task-completed notification for assignee and admins."""
        recipients = await self.get_admin_recipient_ids()
        if task.assigned_to:
            recipients.append(task.assigned_to)
        recipients = list(dict.fromkeys(recipients))
        if not recipients:
            return 0

        created = await self.create_bulk_notifications(
            user_ids=recipients,
            notification_type=NotificationType.TASK_COMPLETED,
            title="Task completed",
            message=f"Task completed: {task.title}",
            payload={"task_id": str(task.id), "workflow_id": str(task.workflow_id)},
            commit=False,
        )
        if commit and created:
            await self.db.commit()
        return created

    async def create_workflow_event_notifications(
        self,
        recipient_ids: list[UUID],
        employee_name: str,
        workflow_id: UUID,
        events: list[dict],
        commit: bool = True,
    ) -> int:
        """Create notifications for workflow and AI orchestration events."""
        created = 0
        unique_recipients = list(dict.fromkeys(recipient_ids))

        for event in events:
            mapping = self._map_event(event, employee_name)
            if not mapping:
                continue
            notification_type, title, message = mapping
            created += await self.create_bulk_notifications(
                user_ids=unique_recipients,
                notification_type=notification_type,
                title=title,
                message=message,
                payload={
                    "workflow_id": str(workflow_id),
                    "event_type": event.get("event_type"),
                    "state_from": event.get("state_from"),
                    "state_to": event.get("state_to"),
                    "payload": event.get("payload"),
                },
                commit=False,
            )

            recipient_emails = await self._resolve_user_emails(unique_recipients)
            for recipient_email in recipient_emails:
                self.send_email_notification(
                    recipient_email=recipient_email,
                    subject=title,
                    _body=message,
                )

        if commit and created:
            await self.db.commit()
        return created

    async def create_ai_indexing_completed_notification(
        self,
        user_id: UUID,
        document_name: str,
        chunks_indexed: int,
        commit: bool = True,
    ) -> Notification:
        """Create notification after document indexing completes."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.AI_INDEXING_COMPLETED,
            title="AI indexing completed",
            message=f"{document_name} indexed successfully with {chunks_indexed} chunks.",
            payload={"document_name": document_name, "chunks_indexed": chunks_indexed},
            commit=commit,
        )

    def send_email_notification(
        self,
        recipient_email: str,
        subject: str,
        _body: str,
    ) -> bool:
        """Best-effort email notification sender via SMTP."""
        sent = self.email_service.send(recipient_email, subject, _body)
        self.logger.info(
            "smtp_notification_attempted",
            extra={
                "recipient_email": recipient_email,
                "subject": subject,
                "delivered": sent,
            },
        )
        return sent

    async def send_welcome_email(
        self,
        employee_email: str,
        employee_name: str,
        employee_id: str,
        company_email: str,
        department: str,
        designation: str,
        manager_id: UUID | None,
        joining_date: str,
        workflow_status: str,
    ) -> None:
        """Send a welcome email to the employee, their manager, and HR."""
        subject = f"Welcome to Amzur Infotech – Your Onboarding Has Started, {employee_name}!"
        body = (
            f"Dear {employee_name},\n\n"
            "Welcome to Amzur Infotech! We are thrilled to have you on board. "
            "Your onboarding process has been initiated and our HR team is ready to support you every step of the way.\n\n"
            "── YOUR DETAILS ──────────────────────────────────\n"
            f"  Employee Name   : {employee_name}\n"
            f"  Employee ID     : {employee_id}\n"
            f"  Company Email   : {company_email}\n"
            f"  Department      : {department}\n"
            f"  Designation     : {designation}\n"
            f"  Start Date      : {joining_date}\n"
            f"  Workflow Status : {workflow_status}\n\n"
            "── ONBOARDING DOCUMENTS & RESOURCES ─────────────\n"
            "Please review the following before your first day:\n\n"
            "  1. Employee Handbook\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  2. Code of Conduct & Company Policies\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  3. IT & Security Guidelines\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  4. Benefits & Payroll Information\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  5. NDA & Compliance Forms (to be signed on Day 1)\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "── NEXT STEPS ────────────────────────────────────\n"
            "  - Your HR team will reach out to schedule your orientation meeting\n"
            "  - IT will provision your accounts (email, Slack, GitHub) before your start date\n"
            "  - Log in to the onboarding portal at https://employees.amzur.com\n\n"
            "If you have any questions, please reply to this email or contact hr@amzur.com.\n\n"
            "We look forward to seeing you on your first day!\n\n"
            "Best regards,\n"
            "HR Team\n"
            "Amzur Infotech\n"
            "hr@amzur.com | +1 (800) AMZUR-HR"
        )

        recipients: list[str] = [employee_email]

        # Add manager email if available
        if manager_id:
            manager_result = await self.db.execute(
                select(User.email).where(
                    and_(User.id == manager_id, User.is_active.is_(True))
                )
            )
            manager_email = manager_result.scalars().first()
            if manager_email:
                recipients.append(manager_email)

        # Add HR/admin recipients
        hr_result = await self.db.execute(
            select(User.email).where(
                and_(
                    User.is_active.is_(True),
                    User.role.in_(["admin", "hr_admin"]),
                    User.email.is_not(None),
                )
            )
        )
        hr_emails = [row[0] for row in hr_result.all() if row[0]]
        recipients.extend(hr_emails)

        unique_recipients = list(dict.fromkeys(recipients))
        sent = self.email_service.send_to_recipients(unique_recipients, subject, body)
        self.logger.info(
            "welcome_email_sent",
            extra={"employee_email": employee_email, "recipients": len(unique_recipients), "delivered": sent},
        )

    async def send_documents_email(
        self,
        employee_email: str,
        employee_name: str,
        company_email: str,
        department: str,
        manager_id: UUID | None,
    ) -> None:
        """Send onboarding documents and company policy links when documents_shared stage is reached."""
        subject = f"Amzur Infotech – Your Onboarding Documents are Ready, {employee_name}"
        body = (
            f"Dear {employee_name},\n\n"
            "Great news! Your onboarding documents and company policies are now ready for you to review.\n\n"
            "── REQUIRED READING (please complete before Day 1) ──\n\n"
            "  1. Employee Handbook\n"
            "     Everything you need to know about working at Amzur Infotech.\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  2. Code of Conduct & Company Policies\n"
            "     Our standards for professional behaviour and workplace ethics.\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  3. IT & Information Security Guidelines\n"
            "     Acceptable use of company systems, data handling, and security requirements.\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  4. Benefits & Payroll Information\n"
            "     Health insurance, PTO policy, payroll schedule, and perks.\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "── DOCUMENTS TO SIGN ON DAY 1 ───────────────────\n\n"
            "  5. Non-Disclosure Agreement (NDA)\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  6. Compliance & Data Privacy Forms\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "  7. Employment Agreement Acknowledgement\n"
            "     https://drive.google.com/drive/u/0/folders/1ACuCqENGL2ZQ6FtsRrLKIX7qlF_x_gb6\n\n"
            "── ONBOARDING PORTAL ────────────────────────────\n\n"
            "  Track your onboarding progress at: https://employees.amzur.com\n"
            f"  Your company email: {company_email}\n\n"
            "Please review all documents before your start date. "
            "If you have any questions, contact hr@amzur.com.\n\n"
            "Best regards,\n"
            "HR Team\n"
            "Amzur Infotech\n"
            "hr@amzur.com | +1 (800) AMZUR-HR"
        )

        recipients: list[str] = [employee_email]

        if manager_id:
            manager_result = await self.db.execute(
                select(User.email).where(and_(User.id == manager_id, User.is_active.is_(True)))
            )
            manager_email = manager_result.scalars().first()
            if manager_email:
                recipients.append(manager_email)

        unique_recipients = list(dict.fromkeys(recipients))
        sent = self.email_service.send_to_recipients(unique_recipients, subject, body)
        self.logger.info(
            "documents_email_sent",
            extra={"employee_email": employee_email, "recipients": len(unique_recipients), "delivered": sent},
        )

    async def send_milestone_email(
        self,
        milestone: str,
        employee_email: str,
        employee_name: str,
        company_email: str,
        department: str,
        manager_id: UUID | None,
    ) -> None:
        """Send a workflow milestone email to employee, manager, and HR."""
        subject = f"Amzur Infotech – Onboarding Update: {milestone} for {employee_name}"

        # When documents_shared milestone is reached, delegate to the richer documents email
        if milestone == "Documents Shared":
            await self.send_documents_email(
                employee_email=employee_email,
                employee_name=employee_name,
                company_email=company_email,
                department=department,
                manager_id=manager_id,
            )
            return

        body = (
            f"Dear {employee_name},\n\n"
            f"Your onboarding at Amzur Infotech has reached a new milestone: {milestone}.\n\n"
            f"  Employee Name : {employee_name}\n"
            f"  Company Email : {company_email}\n"
            f"  Department    : {department}\n"
            f"  Milestone     : {milestone}\n\n"
            "Your HR team will follow up with further instructions.\n\n"
            "Track your progress: https://onboarding.amzur.com\n\n"
            "Best regards,\n"
            "HR Team\n"
            "Amzur Infotech\n"
            "hr@amzur.com"
        )

        recipients: list[str] = [employee_email]

        if manager_id:
            manager_result = await self.db.execute(
                select(User.email).where(
                    and_(User.id == manager_id, User.is_active.is_(True))
                )
            )
            manager_email = manager_result.scalars().first()
            if manager_email:
                recipients.append(manager_email)

        hr_result = await self.db.execute(
            select(User.email).where(
                and_(
                    User.is_active.is_(True),
                    User.role.in_(["admin", "hr_admin"]),
                    User.email.is_not(None),
                )
            )
        )
        hr_emails = [row[0] for row in hr_result.all() if row[0]]
        recipients.extend(hr_emails)

        unique_recipients = list(dict.fromkeys(recipients))
        sent = self.email_service.send_to_recipients(unique_recipients, subject, body)
        self.logger.info(
            "milestone_email_sent",
            extra={
                "milestone": milestone,
                "employee_email": employee_email,
                "recipients": len(unique_recipients),
                "delivered": sent,
            },
        )


    async def _resolve_user_emails(self, user_ids: list[UUID]) -> list[str]:
        if not user_ids:
            return []
        result = await self.db.execute(
            select(User.email).where(
                and_(
                    User.id.in_(user_ids),
                    User.is_active.is_(True),
                    User.email.is_not(None),
                )
            )
        )
        return [row[0] for row in result.all() if row[0]]

    def _map_event(
        self,
        event: dict,
        employee_name: str,
    ) -> tuple[NotificationType, str, str] | None:
        event_type = event.get("event_type")
        state_to = event.get("state_to")

        meeting_mapping = self._map_meeting_event(event)
        if meeting_mapping:
            return meeting_mapping

        if event_type == "workflow_started":
            return (
                NotificationType.WORKFLOW_STARTED,
                "Workflow started",
                f"Onboarding workflow started for {employee_name}.",
            )

        if event_type == "workflow_paused":
            return (
                NotificationType.WORKFLOW_TRANSITION,
                "Workflow paused",
                event.get("message", "Workflow was paused."),
            )

        if event_type == "workflow_resumed":
            return (
                NotificationType.WORKFLOW_TRANSITION,
                "Workflow resumed",
                event.get("message", "Workflow was resumed."),
            )

        if event_type == "workflow_state_changed":
            if state_to == "hr_review":
                return (
                    NotificationType.ONBOARDING_APPROVED,
                    "Onboarding approved",
                    f"{employee_name} moved to HR review.",
                )
            if state_to == "provisioning":
                return (
                    NotificationType.HR_REVIEW_COMPLETED,
                    "HR Review Completed",
                    f"HR review completed for {employee_name}. IT provisioning has started.",
                )
            if state_to == "meetings_scheduled":
                return (
                    NotificationType.IT_PROVISIONING_COMPLETED,
                    "IT Provisioning Completed",
                    f"IT provisioning completed for {employee_name}. Meetings are being scheduled.",
                )
            if state_to == "documents_shared":
                return (
                    NotificationType.DOCUMENTS_SHARED,
                    "Documents Shared",
                    f"Onboarding documents have been shared with {employee_name}.",
                )
            if state_to == "completed":
                return (
                    NotificationType.ONBOARDING_COMPLETED,
                    "Onboarding completed",
                    f"Onboarding completed for {employee_name}.",
                )
            return (
                NotificationType.WORKFLOW_TRANSITION,
                "Workflow transitioned",
                event.get("message", "Workflow state changed."),
            )

        if event_type == "workflow_completed":
            return (
                NotificationType.ONBOARDING_COMPLETED,
                "Onboarding completed",
                f"Onboarding completed for {employee_name}.",
            )

        if event_type in {"tasks_generated", "tasks_assigned"}:
            return (
                NotificationType.AI_ORCHESTRATION,
                "AI orchestration update",
                event.get("message", "AI orchestration generated new updates."),
            )

        if event_type == "escalation":
            return (
                NotificationType.ESCALATION,
                "Onboarding escalation",
                event.get("message", "An onboarding escalation was triggered."),
            )

        return None

    def _map_meeting_event(self, event: dict) -> tuple[NotificationType, str, str] | None:
        event_type = event.get("event_type")
        meeting_event_map: dict[str, tuple[str, str]] = {
            "meeting_scheduled": ("Meeting scheduled", "A meeting has been scheduled."),
            "meeting_updated": ("Meeting updated", "A meeting has been updated."),
            "meeting_cancelled": ("Meeting cancelled", "A meeting has been cancelled."),
        }

        mapped = meeting_event_map.get(event_type)
        if not mapped:
            return None

        title, fallback_message = mapped
        return (
            NotificationType.WORKFLOW_TRANSITION,
            title,
            event.get("message", fallback_message),
        )

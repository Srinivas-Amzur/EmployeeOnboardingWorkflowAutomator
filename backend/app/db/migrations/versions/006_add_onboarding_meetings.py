"""Add onboarding meetings table.

Revision ID: 006_add_onboarding_meetings
Revises: 005_add_notifications
Create Date: 2026-06-07

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "006_add_onboarding_meetings"
down_revision = "005_add_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_meetings",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("meeting_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("meeting_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="scheduled"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["onboarding_workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_onboarding_meetings_employee_id"), "onboarding_meetings", ["employee_id"], unique=False)
    op.create_index(op.f("ix_onboarding_meetings_workflow_id"), "onboarding_meetings", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_onboarding_meetings_meeting_type"), "onboarding_meetings", ["meeting_type"], unique=False)
    op.create_index(op.f("ix_onboarding_meetings_scheduled_for"), "onboarding_meetings", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_onboarding_meetings_status"), "onboarding_meetings", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_onboarding_meetings_status"), table_name="onboarding_meetings")
    op.drop_index(op.f("ix_onboarding_meetings_scheduled_for"), table_name="onboarding_meetings")
    op.drop_index(op.f("ix_onboarding_meetings_meeting_type"), table_name="onboarding_meetings")
    op.drop_index(op.f("ix_onboarding_meetings_workflow_id"), table_name="onboarding_meetings")
    op.drop_index(op.f("ix_onboarding_meetings_employee_id"), table_name="onboarding_meetings")
    op.drop_table("onboarding_meetings")

"""Add onboarding orchestration events table.

Revision ID: 004_add_orchestration_events
Revises: 003_fix_datetime_columns
Create Date: 2026-05-25

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_add_orchestration_events"
down_revision = "003_fix_datetime_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_orchestration_events",
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("state_from", sa.String(length=50), nullable=True),
        sa.Column("state_to", sa.String(length=50), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["onboarding_workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_onboarding_orchestration_events_workflow_id"), "onboarding_orchestration_events", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_onboarding_orchestration_events_employee_id"), "onboarding_orchestration_events", ["employee_id"], unique=False)
    op.create_index(op.f("ix_onboarding_orchestration_events_event_type"), "onboarding_orchestration_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_onboarding_orchestration_events_event_type"), table_name="onboarding_orchestration_events")
    op.drop_index(op.f("ix_onboarding_orchestration_events_employee_id"), table_name="onboarding_orchestration_events")
    op.drop_index(op.f("ix_onboarding_orchestration_events_workflow_id"), table_name="onboarding_orchestration_events")
    op.drop_table("onboarding_orchestration_events")

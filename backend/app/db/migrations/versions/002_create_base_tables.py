"""Create base tables if missing.

Revision ID: 002_create_base_tables
Revises: 001_initial
Create Date: 2026-05-25

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Alembic identifiers
revision = "002_create_base_tables"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def _has_table(bind: sa.engine.Connection, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_table(bind, "users"):
        op.create_table(
            "users",
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=True),
            sa.Column("google_id", sa.String(length=255), nullable=True),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    if not _has_table(bind, "employees"):
        op.create_table(
            "employees",
            sa.Column("first_name", sa.String(length=255), nullable=False),
            sa.Column("last_name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("department", sa.String(length=255), nullable=False),
            sa.Column("designation", sa.String(length=255), nullable=False),
            sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("joining_date", sa.Date(), nullable=False),
            sa.Column("onboarding_status", sa.String(length=50), nullable=False),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["manager_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index(op.f("ix_employees_email"), "employees", ["email"], unique=False)

    if not _has_table(bind, "onboarding_workflows"):
        op.create_table(
            "onboarding_workflows",
            sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("current_state", sa.String(length=50), nullable=False),
            sa.Column("completion_percentage", sa.Integer(), nullable=False),
            sa.Column("started_at", sa.String(length=50), nullable=False),
            sa.Column("completed_at", sa.String(length=50), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table(bind, "onboarding_tasks"):
        op.create_table(
            "onboarding_tasks",
            sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("priority", sa.String(length=50), nullable=False),
            sa.Column("due_date", sa.String(length=50), nullable=True),
            sa.Column("completed_at", sa.String(length=50), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
            sa.ForeignKeyConstraint(["workflow_id"], ["onboarding_workflows.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _has_table(bind, "onboarding_tasks"):
        op.drop_table("onboarding_tasks")

    if _has_table(bind, "onboarding_workflows"):
        op.drop_table("onboarding_workflows")

    if _has_table(bind, "employees"):
        op.drop_index(op.f("ix_employees_email"), table_name="employees")
        op.drop_table("employees")

    if _has_table(bind, "users"):
        op.drop_index(op.f("ix_users_email"), table_name="users")
        op.drop_table("users")

"""Add performance indexes for all hot query paths.

Revision ID: 008_performance_indexes
Revises: 007_add_company_email
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa

revision = "008_performance_indexes"
down_revision = "007_add_company_email"
branch_labels = None
depends_on = None


def _idx(table: str, cols: list[str], unique: bool = False) -> str:
    return f"ix_{table}_{'_'.join(cols)}"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_index(table: str, name: str) -> bool:
        return any(idx["name"] == name for idx in inspector.get_indexes(table))

    def create(table: str, cols: list[str], unique: bool = False) -> None:
        name = _idx(table, cols)
        if not has_index(table, name):
            op.create_index(name, table, cols, unique=unique)

    # ── employees ─────────────────────────────────────────────────────────────
    # Filters: onboarding_status, department; sort: created_at DESC
    create("employees", ["onboarding_status"])
    create("employees", ["department"])
    create("employees", ["joining_date"])
    create("employees", ["created_at"])
    # Composite: list_employees filters department + status together
    create("employees", ["department", "onboarding_status"])

    # ── onboarding_workflows ──────────────────────────────────────────────────
    # GROUP BY current_state for analytics; filter by employee_id + created_at
    create("onboarding_workflows", ["employee_id"])
    create("onboarding_workflows", ["current_state"])
    create("onboarding_workflows", ["created_at"])
    # Composite for analytics: avg(completion_percentage) where completed_at IS NOT NULL
    create("onboarding_workflows", ["completed_at"])
    # Dashboard: GROUP BY current_state — partial composite speeds count
    create("onboarding_workflows", ["current_state", "employee_id"])

    # ── onboarding_tasks ──────────────────────────────────────────────────────
    # Heavily queried: GROUP BY status, filter workflow_id + status
    create("onboarding_tasks", ["workflow_id"])
    create("onboarding_tasks", ["status"])
    create("onboarding_tasks", ["assigned_to"])
    # Composite — most common access pattern: tasks for a workflow by status
    create("onboarding_tasks", ["workflow_id", "status"])

    # ── onboarding_meetings ───────────────────────────────────────────────────
    # Already has employee_id, workflow_id, meeting_type, scheduled_for, status
    # Add composite for "upcoming meetings" query
    create("onboarding_meetings", ["status", "scheduled_for"])
    create("onboarding_meetings", ["employee_id", "status"])

    # ── notifications ─────────────────────────────────────────────────────────
    # Already has user_id, notification_type, is_read
    # Hot path: list for user ordered by created_at DESC; unread count
    create("notifications", ["user_id", "is_read"])
    create("notifications", ["user_id", "created_at"])
    # Analytics queries: COUNT WHERE notification_type = 'ai_orchestration'
    create("notifications", ["notification_type", "created_at"])

    # ── onboarding_orchestration_events ──────────────────────────────────────
    # Queried by workflow_id + event_type; ordered created_at ASC/DESC
    create("onboarding_orchestration_events", ["workflow_id"])
    create("onboarding_orchestration_events", ["employee_id"])
    create("onboarding_orchestration_events", ["event_type"])
    create("onboarding_orchestration_events", ["workflow_id", "event_type"])
    create("onboarding_orchestration_events", ["workflow_id", "created_at"])

    # ── users ─────────────────────────────────────────────────────────────────
    # Admin lookups by role (get_admin_recipient_ids fires on every task/meeting)
    create("users", ["role"])
    create("users", ["is_active"])
    create("users", ["role", "is_active"])


def downgrade() -> None:
    tables_cols = [
        ("employees",                       ["onboarding_status"]),
        ("employees",                       ["department"]),
        ("employees",                       ["joining_date"]),
        ("employees",                       ["created_at"]),
        ("employees",                       ["department", "onboarding_status"]),
        ("onboarding_workflows",            ["employee_id"]),
        ("onboarding_workflows",            ["current_state"]),
        ("onboarding_workflows",            ["created_at"]),
        ("onboarding_workflows",            ["completed_at"]),
        ("onboarding_workflows",            ["current_state", "employee_id"]),
        ("onboarding_tasks",                ["workflow_id"]),
        ("onboarding_tasks",                ["status"]),
        ("onboarding_tasks",                ["assigned_to"]),
        ("onboarding_tasks",                ["workflow_id", "status"]),
        ("onboarding_meetings",             ["status", "scheduled_for"]),
        ("onboarding_meetings",             ["employee_id", "status"]),
        ("notifications",                   ["user_id", "is_read"]),
        ("notifications",                   ["user_id", "created_at"]),
        ("notifications",                   ["notification_type", "created_at"]),
        ("onboarding_orchestration_events", ["workflow_id"]),
        ("onboarding_orchestration_events", ["employee_id"]),
        ("onboarding_orchestration_events", ["event_type"]),
        ("onboarding_orchestration_events", ["workflow_id", "event_type"]),
        ("onboarding_orchestration_events", ["workflow_id", "created_at"]),
        ("users",                           ["role"]),
        ("users",                           ["is_active"]),
        ("users",                           ["role", "is_active"]),
    ]
    for table, cols in tables_cols:
        try:
            op.drop_index(_idx(table, cols), table_name=table)
        except Exception:  # noqa: BLE001
            pass

"""Fix datetime columns in onboarding_workflows and onboarding_tasks.

Revision ID: 003_fix_datetime_columns
Revises: 002_create_base_tables
Create Date: 2026-05-25

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_fix_datetime_columns"
down_revision = "002_create_base_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # --- onboarding_workflows -------------------------------------------------
    if inspector.has_table("onboarding_workflows"):
        cols = {c["name"]: c for c in inspector.get_columns("onboarding_workflows")}

        if "started_at" in cols and not str(cols["started_at"]["type"]).startswith("TIMESTAMP"):
            # Convert existing string values then change type
            op.execute(
                "ALTER TABLE onboarding_workflows "
                "ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE "
                "USING CASE WHEN started_at ~ '^\\d' "
                "THEN started_at::TIMESTAMP WITH TIME ZONE "
                "ELSE NOW() END"
            )

        if "completed_at" in cols and not str(cols["completed_at"]["type"]).startswith("TIMESTAMP"):
            op.execute(
                "ALTER TABLE onboarding_workflows "
                "ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE "
                "USING CASE WHEN completed_at IS NOT NULL AND completed_at ~ '^\\d' "
                "THEN completed_at::TIMESTAMP WITH TIME ZONE "
                "ELSE NULL END"
            )

    # --- onboarding_tasks -----------------------------------------------------
    if inspector.has_table("onboarding_tasks"):
        cols = {c["name"]: c for c in inspector.get_columns("onboarding_tasks")}

        if "due_date" in cols and not str(cols["due_date"]["type"]).startswith("TIMESTAMP"):
            op.execute(
                "ALTER TABLE onboarding_tasks "
                "ALTER COLUMN due_date TYPE TIMESTAMP WITH TIME ZONE "
                "USING CASE WHEN due_date IS NOT NULL AND due_date ~ '^\\d' "
                "THEN due_date::TIMESTAMP WITH TIME ZONE "
                "ELSE NULL END"
            )

        if "completed_at" in cols and not str(cols["completed_at"]["type"]).startswith("TIMESTAMP"):
            op.execute(
                "ALTER TABLE onboarding_tasks "
                "ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE "
                "USING CASE WHEN completed_at IS NOT NULL AND completed_at ~ '^\\d' "
                "THEN completed_at::TIMESTAMP WITH TIME ZONE "
                "ELSE NULL END"
            )


def downgrade() -> None:
    # Revert to VARCHAR — lossy but reversible for dev
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("onboarding_workflows"):
        op.execute(
            "ALTER TABLE onboarding_workflows "
            "ALTER COLUMN started_at TYPE VARCHAR(50) USING started_at::TEXT"
        )
        op.execute(
            "ALTER TABLE onboarding_workflows "
            "ALTER COLUMN completed_at TYPE VARCHAR(50) USING completed_at::TEXT"
        )

    if inspector.has_table("onboarding_tasks"):
        op.execute(
            "ALTER TABLE onboarding_tasks "
            "ALTER COLUMN due_date TYPE VARCHAR(50) USING due_date::TEXT"
        )
        op.execute(
            "ALTER TABLE onboarding_tasks "
            "ALTER COLUMN completed_at TYPE VARCHAR(50) USING completed_at::TEXT"
        )

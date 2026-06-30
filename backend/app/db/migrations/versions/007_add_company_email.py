"""Add company_email column to employees table.

Revision ID: 007_add_company_email
Revises: 006_add_onboarding_meetings
Create Date: 2026-06-29

"""

from alembic import op
import sqlalchemy as sa


revision = "007_add_company_email"
down_revision = "006_add_onboarding_meetings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("company_email", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_employees_company_email"),
        "employees",
        ["company_email"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_employees_company_email"), table_name="employees")
    op.drop_column("employees", "company_email")

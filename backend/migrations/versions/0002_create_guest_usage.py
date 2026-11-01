"""create guest_usage

Revision ID: 0002_create_guest_usage
Revises: 0001_create_users
Create Date: 2026-10-28
"""
# pylint: disable=invalid-name

from alembic import op
import sqlalchemy as sa

revision = "0002_create_guest_usage"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the guest_usage table."""
    op.create_table(
        "guest_usage",
        sa.Column("guest_id", sa.Uuid(), primary_key=True),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("message_count >= 0", name="ck_guest_usage_count_non_negative"),
    )


def downgrade() -> None:
    """Drop the guest_usage table."""
    op.drop_table("guest_usage")

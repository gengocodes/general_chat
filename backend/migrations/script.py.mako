"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
# pylint: disable=invalid-name

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Apply schema upgrade."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Revert schema upgrade."""
    ${downgrades if downgrades else "pass"}

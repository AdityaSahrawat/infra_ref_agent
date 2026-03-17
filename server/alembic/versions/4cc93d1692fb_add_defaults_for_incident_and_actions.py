"""add defaults for incident and actions

Revision ID: 4cc93d1692fb
Revises: 05ef24676a17
Create Date: 2026-03-17 10:46:48.012082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cc93d1692fb'
down_revision: Union[str, Sequence[str], None] = '05ef24676a17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Backfill any existing NULLs before enforcing/adding defaults
    op.execute("UPDATE incident SET matric_summary = '' WHERE matric_summary IS NULL")
    op.execute("UPDATE actions SET status = 'pending' WHERE status IS NULL")

    op.alter_column(
        "incident",
        "matric_summary",
        existing_type=sa.Text(),
        nullable=False,
        server_default="",
    )

    op.alter_column(
        "actions",
        "status",
        existing_type=sa.Text(),
        nullable=False,
        server_default="pending",
    )

    # Optional but helpful: align timestamps with DB defaults as well
    op.alter_column(
        "incident",
        "receivedAt",
        existing_type=sa.TIMESTAMP(),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    op.alter_column(
        "incident",
        "created_at",
        existing_type=sa.TIMESTAMP(),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "incident",
        "created_at",
        existing_type=sa.TIMESTAMP(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "incident",
        "receivedAt",
        existing_type=sa.TIMESTAMP(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "actions",
        "status",
        existing_type=sa.Text(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "incident",
        "matric_summary",
        existing_type=sa.Text(),
        nullable=False,
        server_default=None,
    )

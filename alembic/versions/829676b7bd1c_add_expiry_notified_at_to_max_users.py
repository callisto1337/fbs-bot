"""add expiry_notified_at to max_users

Revision ID: 829676b7bd1c
Revises: 98bd89a04d51
Create Date: 2026-09-18 11:57:32.298133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '829676b7bd1c'
down_revision: Union[str, Sequence[str], None] = '98bd89a04d51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "max_users",
        sa.Column("expiry_notified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("max_users", "expiry_notified_at")

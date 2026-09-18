"""create max_users table

Revision ID: 98bd89a04d51
Revises: 
Create Date: 2026-09-18 11:57:31.631493

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98bd89a04d51'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "max_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("max_user_id", sa.BigInteger(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_max_users_phone"), "max_users", ["phone"], unique=True)
    op.create_index(
        op.f("ix_max_users_max_user_id"), "max_users", ["max_user_id"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_max_users_max_user_id"), table_name="max_users")
    op.drop_index(op.f("ix_max_users_phone"), table_name="max_users")
    op.drop_table("max_users")

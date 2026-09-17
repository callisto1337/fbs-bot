"""create max_users

Revision ID: 9f38a2c1e001
Revises:
Create Date: 2026-09-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "9f38a2c1e001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "max_users",
        sa.Column("id", sa.Integer(), primary_key=True),
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
    )
    op.create_index(
        "ix_max_users_phone", "max_users", ["phone"], unique=True
    )
    op.create_index(
        "ix_max_users_max_user_id", "max_users", ["max_user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_max_users_max_user_id", table_name="max_users")
    op.drop_index("ix_max_users_phone", table_name="max_users")
    op.drop_table("max_users")

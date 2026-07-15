"""add affiliation to users allowlist

Revision ID: 0002_user_affiliation
Revises: 0001_users
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_user_affiliation"
down_revision: Union[str, None] = "0001_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("affiliation", sa.String(length=255), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("users", "affiliation")

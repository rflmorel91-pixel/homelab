"""Add tenant timezone

Revision ID: b5d8f2e3a901
Revises: a4c7e1d2f890
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5d8f2e3a901"
down_revision: Union[str, Sequence[str], None] = (
    "a4c7e1d2f890"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "timezone_name",
            sa.String(length=100),
            server_default="UTC",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "tenants",
        "timezone_name",
    )

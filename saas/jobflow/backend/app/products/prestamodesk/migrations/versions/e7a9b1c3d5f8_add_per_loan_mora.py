"""add per-loan prestamodesk mora selection

Revision ID: e7a9b1c3d5f8
Revises: d6f8a0b2c4e7
Create Date: 2026-10-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e7a9b1c3d5f8"
down_revision: str | None = "d6f8a0b2c4e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "prestamodesk_loans",
        sa.Column(
            "late_fee_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )

    op.alter_column(
        "prestamodesk_loans",
        "late_fee_enabled",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column(
        "prestamodesk_loans",
        "late_fee_enabled",
    )

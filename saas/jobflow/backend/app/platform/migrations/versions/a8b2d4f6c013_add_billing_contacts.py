"""Add billing contacts

Revision ID: a8b2d4f6c013
Revises: f7a1c3e5b902
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8b2d4f6c013"
down_revision: Union[str, Sequence[str], None] = (
    "f7a1c3e5b902"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "platform_billing_accounts",
        sa.Column(
            "billing_contact_name",
            sa.String(length=200),
            nullable=True,
        ),
    )

    op.add_column(
        "platform_billing_accounts",
        sa.Column(
            "billing_contact_email",
            sa.String(length=320),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "platform_billing_accounts",
        "billing_contact_email",
    )

    op.drop_column(
        "platform_billing_accounts",
        "billing_contact_name",
    )

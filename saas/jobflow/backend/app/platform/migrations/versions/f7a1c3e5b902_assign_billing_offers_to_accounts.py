"""Assign billing offers to billing accounts

Revision ID: f7a1c3e5b902
Revises: e6c9b2d4f103
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7a1c3e5b902"
down_revision: Union[str, Sequence[str], None] = (
    "e6c9b2d4f103"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "platform_billing_accounts",
        sa.Column(
            "billing_offer_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_platform_billing_accounts_offer",
        "platform_billing_accounts",
        "platform_billing_offers",
        ["billing_offer_id"],
        ["id"],
    )

    op.create_index(
        "ix_platform_billing_accounts_billing_offer_id",
        "platform_billing_accounts",
        ["billing_offer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_platform_billing_accounts_billing_offer_id",
        table_name="platform_billing_accounts",
    )

    op.drop_constraint(
        "fk_platform_billing_accounts_offer",
        "platform_billing_accounts",
        type_="foreignkey",
    )

    op.drop_column(
        "platform_billing_accounts",
        "billing_offer_id",
    )

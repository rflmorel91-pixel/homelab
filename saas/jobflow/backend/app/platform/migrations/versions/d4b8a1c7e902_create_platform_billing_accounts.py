"""Create platform billing accounts

Revision ID: d4b8a1c7e902
Revises: a7f3c2d9e401
Create Date: 2026-08-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4b8a1c7e902"
down_revision: Union[str, Sequence[str], None] = (
    "a7f3c2d9e401"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_billing_accounts",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "billing_mode",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "provider_customer_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "provider_subscription_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            name=(
                "uq_platform_billing_accounts_"
                "tenant_id"
            ),
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "platform_billing_accounts"
    )

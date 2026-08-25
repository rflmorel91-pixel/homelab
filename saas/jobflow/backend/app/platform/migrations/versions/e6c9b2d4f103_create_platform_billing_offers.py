"""Create platform billing offers

Revision ID: e6c9b2d4f103
Revises: d4b8a1c7e902
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6c9b2d4f103"
down_revision: Union[str, Sequence[str], None] = (
    "d4b8a1c7e902"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_billing_offers",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "charge_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "minimum_amount_cents",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "maximum_amount_cents",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "billing_interval",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "service_period_days",
            sa.Integer(),
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
        sa.CheckConstraint(
            (
                "minimum_amount_cents IS NULL "
                "OR minimum_amount_cents >= 0"
            ),
            name=(
                "ck_platform_billing_offers_"
                "minimum_amount"
            ),
        ),
        sa.CheckConstraint(
            (
                "maximum_amount_cents IS NULL "
                "OR maximum_amount_cents >= 0"
            ),
            name=(
                "ck_platform_billing_offers_"
                "maximum_amount"
            ),
        ),
        sa.CheckConstraint(
            (
                "minimum_amount_cents IS NULL "
                "OR maximum_amount_cents IS NULL "
                "OR minimum_amount_cents "
                "<= maximum_amount_cents"
            ),
            name=(
                "ck_platform_billing_offers_"
                "amount_range"
            ),
        ),
        sa.CheckConstraint(
            (
                "service_period_days IS NULL "
                "OR service_period_days > 0"
            ),
            name=(
                "ck_platform_billing_offers_"
                "service_period"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "code",
            name=(
                "uq_platform_billing_offers_"
                "product_code"
            ),
        ),
    )

    op.create_index(
        "ix_platform_billing_offers_product_id",
        "platform_billing_offers",
        ["product_id"],
        unique=False,
    )

    op.create_index(
        "ix_platform_billing_offers_status",
        "platform_billing_offers",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_platform_billing_offers_status",
        table_name="platform_billing_offers",
    )

    op.drop_index(
        "ix_platform_billing_offers_product_id",
        table_name="platform_billing_offers",
    )

    op.drop_table(
        "platform_billing_offers"
    )

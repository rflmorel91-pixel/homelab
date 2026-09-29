"""Add PréstamoDesk vehicle loan fields

Revision ID: 9b2d4f6a8c1e
Revises: 7c9e1a3b5d6f
Create Date: 2026-09-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b2d4f6a8c1e"
down_revision: Union[str, Sequence[str], None] = (
    "7c9e1a3b5d6f"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prestamodesk_loans",
        sa.Column(
            "loan_type",
            sa.String(30),
            server_default="personal",
            nullable=False,
        ),
    )

    for name, column_type in (
        ("vehicle_cash_price", sa.Numeric(14, 2)),
        ("vehicle_down_payment", sa.Numeric(14, 2)),
        ("vehicle_make", sa.String(100)),
        ("vehicle_model", sa.String(100)),
        ("vehicle_year", sa.Integer()),
        ("vehicle_color", sa.String(50)),
        ("vehicle_vin", sa.String(50)),
        ("vehicle_license_plate", sa.String(30)),
        ("vehicle_seller", sa.String(200)),
        ("vehicle_notes", sa.Text()),
    ):
        op.add_column(
            "prestamodesk_loans",
            sa.Column(
                name,
                column_type,
                nullable=True,
            ),
        )

    op.alter_column(
        "prestamodesk_loans",
        "loan_type",
        server_default=None,
    )


def downgrade() -> None:
    for column in (
        "vehicle_notes",
        "vehicle_seller",
        "vehicle_license_plate",
        "vehicle_vin",
        "vehicle_color",
        "vehicle_year",
        "vehicle_model",
        "vehicle_make",
        "vehicle_down_payment",
        "vehicle_cash_price",
        "loan_type",
    ):
        op.drop_column(
            "prestamodesk_loans",
            column,
        )

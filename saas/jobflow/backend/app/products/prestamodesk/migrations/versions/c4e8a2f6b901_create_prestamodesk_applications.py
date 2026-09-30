"""Create PréstamoDesk applications

Revision ID: c4e8a2f6b901
Revises: 9b2d4f6a8c1e
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8a2f6b901"
down_revision: Union[str, Sequence[str], None] = (
    "9b2d4f6a8c1e"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "converted_borrower_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "converted_loan_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("document_number", sa.String(50), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("municipality", sa.String(120), nullable=True),
        sa.Column("province", sa.String(120), nullable=True),
        sa.Column("loan_type", sa.String(30), nullable=False),
        sa.Column(
            "vehicle_cash_price",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "vehicle_down_payment",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column("vehicle_make", sa.String(100), nullable=False),
        sa.Column("vehicle_model", sa.String(100), nullable=False),
        sa.Column("vehicle_year", sa.Integer(), nullable=False),
        sa.Column("vehicle_color", sa.String(50), nullable=True),
        sa.Column("vehicle_vin", sa.String(50), nullable=True),
        sa.Column(
            "vehicle_license_plate",
            sa.String(30),
            nullable=True,
        ),
        sa.Column("vehicle_seller", sa.String(200), nullable=True),
        sa.Column("vehicle_notes", sa.Text(), nullable=True),
        sa.Column(
            "principal_amount",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "flat_interest_rate_percent",
            sa.Numeric(7, 4),
            nullable=False,
        ),
        sa.Column(
            "total_interest",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "total_due",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column("installment_count", sa.Integer(), nullable=False),
        sa.Column(
            "payment_frequency",
            sa.String(30),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("first_payment_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("consented_at", sa.DateTime(), nullable=False),
        sa.Column(
            "consent_notice_version",
            sa.String(30),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("converted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["converted_borrower_id"],
            ["prestamodesk_borrowers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["converted_loan_id"],
            ["prestamodesk_loans.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("converted_borrower_id"),
        sa.UniqueConstraint("converted_loan_id"),
    )

    for column in (
        "tenant_id",
        "status",
        "created_at",
    ):
        op.create_index(
            op.f(
                f"ix_prestamodesk_applications_{column}"
            ),
            "prestamodesk_applications",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in (
        "created_at",
        "status",
        "tenant_id",
    ):
        op.drop_index(
            op.f(
                f"ix_prestamodesk_applications_{column}"
            ),
            table_name="prestamodesk_applications",
        )

    op.drop_table("prestamodesk_applications")

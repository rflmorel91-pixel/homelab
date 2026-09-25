"""Create PréstamoDesk loans and installments

Revision ID: 2f4a6b8c0d1e
Revises: 8d9e1f2a3b4c
Create Date: 2026-09-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f4a6b8c0d1e"
down_revision: Union[str, Sequence[str], None] = "8d9e1f2a3b4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_loans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("borrower_id", sa.Integer(), nullable=False),
        sa.Column("principal_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "flat_interest_rate_percent",
            sa.Numeric(7, 4),
            nullable=False,
        ),
        sa.Column("total_interest", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_due", sa.Numeric(14, 2), nullable=False),
        sa.Column("installment_count", sa.Integer(), nullable=False),
        sa.Column("payment_frequency", sa.String(30), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("first_payment_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["borrower_id"],
            ["prestamodesk_borrowers.id"],
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_prestamodesk_loans_tenant_id"),
        "prestamodesk_loans",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prestamodesk_loans_borrower_id"),
        "prestamodesk_loans",
        ["borrower_id"],
        unique=False,
    )

    op.create_table(
        "prestamodesk_installments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("principal_due", sa.Numeric(14, 2), nullable=False),
        sa.Column("interest_due", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_due", sa.Numeric(14, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["loan_id"],
            ["prestamodesk_loans.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "loan_id",
            "sequence_number",
            name="uq_prestamodesk_installment_sequence",
        ),
    )

    op.create_index(
        op.f("ix_prestamodesk_installments_tenant_id"),
        "prestamodesk_installments",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prestamodesk_installments_loan_id"),
        "prestamodesk_installments",
        ["loan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prestamodesk_installments_due_date"),
        "prestamodesk_installments",
        ["due_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_prestamodesk_installments_due_date"),
        table_name="prestamodesk_installments",
    )
    op.drop_index(
        op.f("ix_prestamodesk_installments_loan_id"),
        table_name="prestamodesk_installments",
    )
    op.drop_index(
        op.f("ix_prestamodesk_installments_tenant_id"),
        table_name="prestamodesk_installments",
    )
    op.drop_table("prestamodesk_installments")

    op.drop_index(
        op.f("ix_prestamodesk_loans_borrower_id"),
        table_name="prestamodesk_loans",
    )
    op.drop_index(
        op.f("ix_prestamodesk_loans_tenant_id"),
        table_name="prestamodesk_loans",
    )
    op.drop_table("prestamodesk_loans")

"""Create PréstamoDesk payments

Revision ID: 5a7c9e1f3b2d
Revises: 2f4a6b8c0d1e
Create Date: 2026-09-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5a7c9e1f3b2d"
down_revision: Union[str, Sequence[str], None] = "2f4a6b8c0d1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column("installment_id", sa.Integer(), nullable=False),
        sa.Column("recorded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("reference", sa.String(200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["installment_id"],
            ["prestamodesk_installments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["loan_id"],
            ["prestamodesk_loans.id"],
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    for column in (
        "tenant_id",
        "loan_id",
        "installment_id",
        "recorded_by_user_id",
    ):
        op.create_index(
            op.f(
                f"ix_prestamodesk_payments_{column}"
            ),
            "prestamodesk_payments",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in (
        "recorded_by_user_id",
        "installment_id",
        "loan_id",
        "tenant_id",
    ):
        op.drop_index(
            op.f(
                f"ix_prestamodesk_payments_{column}"
            ),
            table_name="prestamodesk_payments",
        )

    op.drop_table("prestamodesk_payments")

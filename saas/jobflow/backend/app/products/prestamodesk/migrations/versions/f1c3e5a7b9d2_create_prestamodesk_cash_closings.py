"""create prestamodesk cash closings

Revision ID: f1c3e5a7b9d2
Revises: e7a9b1c3d5f8
Create Date: 2026-10-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f1c3e5a7b9d2"
down_revision: str | None = "e7a9b1c3d5f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_cash_closings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "cashier_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=False),
        sa.Column("payment_count", sa.Integer(), nullable=False),
        sa.Column(
            "total_collected",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "cash_expected",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "cash_counted",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "cash_difference",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "bank_transfer_total",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "card_total",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "other_total",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["cashier_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_prestamodesk_cash_closings_tenant_id",
        "prestamodesk_cash_closings",
        ["tenant_id"],
    )
    op.create_index(
        "ix_prestamodesk_cash_closings_cashier_user_id",
        "prestamodesk_cash_closings",
        ["cashier_user_id"],
    )
    op.create_index(
        "ix_prestamodesk_cash_closings_closed_at",
        "prestamodesk_cash_closings",
        ["closed_at"],
    )

    op.add_column(
        "prestamodesk_payments",
        sa.Column(
            "cash_closing_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_prestamodesk_payments_cash_closing_id",
        "prestamodesk_payments",
        "prestamodesk_cash_closings",
        ["cash_closing_id"],
        ["id"],
    )
    op.create_index(
        "ix_prestamodesk_payments_cash_closing_id",
        "prestamodesk_payments",
        ["cash_closing_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prestamodesk_payments_cash_closing_id",
        table_name="prestamodesk_payments",
    )
    op.drop_constraint(
        "fk_prestamodesk_payments_cash_closing_id",
        "prestamodesk_payments",
        type_="foreignkey",
    )
    op.drop_column(
        "prestamodesk_payments",
        "cash_closing_id",
    )

    op.drop_index(
        "ix_prestamodesk_cash_closings_closed_at",
        table_name="prestamodesk_cash_closings",
    )
    op.drop_index(
        "ix_prestamodesk_cash_closings_cashier_user_id",
        table_name="prestamodesk_cash_closings",
    )
    op.drop_index(
        "ix_prestamodesk_cash_closings_tenant_id",
        table_name="prestamodesk_cash_closings",
    )
    op.drop_table("prestamodesk_cash_closings")

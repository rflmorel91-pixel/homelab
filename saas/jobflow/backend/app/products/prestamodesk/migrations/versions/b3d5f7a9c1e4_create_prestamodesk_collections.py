"""create prestamodesk collections

Revision ID: b3d5f7a9c1e4
Revises: a2c4e6f8b0d3
Create Date: 2026-10-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b3d5f7a9c1e4"
down_revision: str | None = "a2c4e6f8b0d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_collection_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column(
            "recorded_by_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "outcome",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "contacted_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "next_follow_up_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "channel IN ("
            "'phone', 'whatsapp', 'sms', "
            "'email', 'visit', 'other'"
            ")",
            name=(
                "ck_prestamodesk_collection_activity_channel"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["loan_id"],
            ["prestamodesk_loans.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for column in (
        "tenant_id",
        "loan_id",
        "recorded_by_user_id",
        "contacted_at",
        "next_follow_up_at",
    ):
        op.create_index(
            "ix_prestamodesk_collection_activities_"
            + column,
            "prestamodesk_collection_activities",
            [column],
        )

    op.create_table(
        "prestamodesk_payment_promises",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "promised_amount",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "fulfilled_amount",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "fulfilled_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(),
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
            "status IN ("
            "'pending', 'partial', "
            "'fulfilled', 'cancelled'"
            ")",
            name=(
                "ck_prestamodesk_payment_promise_status"
            ),
        ),
        sa.CheckConstraint(
            "promised_amount > 0",
            name=(
                "ck_prestamodesk_payment_promise_amount"
            ),
        ),
        sa.CheckConstraint(
            "fulfilled_amount >= 0 "
            "AND fulfilled_amount <= promised_amount",
            name=(
                "ck_prestamodesk_payment_promise_fulfilled"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["loan_id"],
            ["prestamodesk_loans.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for column in (
        "tenant_id",
        "loan_id",
        "created_by_user_id",
        "due_date",
        "status",
    ):
        op.create_index(
            "ix_prestamodesk_payment_promises_"
            + column,
            "prestamodesk_payment_promises",
            [column],
        )

    op.create_table(
        "prestamodesk_promise_payment_allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "promise_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "payment_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name=(
                "ck_prestamodesk_promise_payment_allocation_amount"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["promise_id"],
            ["prestamodesk_payment_promises.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["prestamodesk_payments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "promise_id",
            "payment_id",
            name=(
                "uq_prestamodesk_promise_payment_allocation"
            ),
        ),
    )

    for column in (
        "tenant_id",
        "promise_id",
        "payment_id",
    ):
        op.create_index(
            "ix_prestamodesk_promise_payment_allocations_"
            + column,
            "prestamodesk_promise_payment_allocations",
            [column],
        )


def downgrade() -> None:
    for column in (
        "payment_id",
        "promise_id",
        "tenant_id",
    ):
        op.drop_index(
            "ix_prestamodesk_promise_payment_allocations_"
            + column,
            table_name=(
                "prestamodesk_promise_payment_allocations"
            ),
        )

    op.drop_table(
        "prestamodesk_promise_payment_allocations"
    )

    for column in (
        "status",
        "due_date",
        "created_by_user_id",
        "loan_id",
        "tenant_id",
    ):
        op.drop_index(
            "ix_prestamodesk_payment_promises_"
            + column,
            table_name="prestamodesk_payment_promises",
        )

    op.drop_table("prestamodesk_payment_promises")

    for column in (
        "next_follow_up_at",
        "contacted_at",
        "recorded_by_user_id",
        "loan_id",
        "tenant_id",
    ):
        op.drop_index(
            "ix_prestamodesk_collection_activities_"
            + column,
            table_name=(
                "prestamodesk_collection_activities"
            ),
        )

    op.drop_table(
        "prestamodesk_collection_activities"
    )

"""add prestamodesk late fees

Revision ID: d6f8a0b2c4e7
Revises: c4e8a2f6b901
Create Date: 2026-10-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d6f8a0b2c4e7"
down_revision: str | None = "c4e8a2f6b901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_late_fee_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "daily_rate_percent",
            sa.Numeric(7, 4),
            server_default="0.0000",
            nullable=False,
        ),
        sa.Column(
            "grace_days",
            sa.Integer(),
            server_default="5",
            nullable=False,
        ),
        sa.Column(
            "cap_percent",
            sa.Numeric(7, 4),
            server_default="25.0000",
            nullable=False,
        ),
        sa.Column(
            "effective_date",
            sa.Date(),
            nullable=False,
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
            "daily_rate_percent >= 0",
            name="ck_prestamodesk_late_fee_rate_nonnegative",
        ),
        sa.CheckConstraint(
            "grace_days >= 0",
            name="ck_prestamodesk_late_fee_grace_nonnegative",
        ),
        sa.CheckConstraint(
            "cap_percent >= 0",
            name="ck_prestamodesk_late_fee_cap_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id"),
    )
    op.create_index(
        "ix_prestamodesk_late_fee_policies_tenant_id",
        "prestamodesk_late_fee_policies",
        ["tenant_id"],
        unique=True,
    )

    for column_name in (
        "principal_paid",
        "interest_paid",
        "late_fee_accrued",
        "late_fee_paid",
    ):
        op.add_column(
            "prestamodesk_installments",
            sa.Column(
                column_name,
                sa.Numeric(14, 2),
                server_default="0.00",
                nullable=False,
            ),
        )

    op.add_column(
        "prestamodesk_installments",
        sa.Column(
            "late_fee_assessed_through",
            sa.Date(),
            nullable=True,
        ),
    )

    for column_name in (
        "principal_amount",
        "interest_amount",
        "late_fee_amount",
    ):
        op.add_column(
            "prestamodesk_payments",
            sa.Column(
                column_name,
                sa.Numeric(14, 2),
                server_default="0.00",
                nullable=False,
            ),
        )

    op.execute(
        """
        UPDATE prestamodesk_installments
        SET
            interest_paid = LEAST(
                paid_amount,
                interest_due
            ),
            principal_paid = GREATEST(
                paid_amount - interest_due,
                0
            )
        """
    )

    op.execute(
        """
        WITH allocations AS (
            SELECT
                payments.id,
                payments.amount,
                installments.interest_due,
                COALESCE(
                    SUM(payments.amount) OVER (
                        PARTITION BY payments.installment_id
                        ORDER BY payments.paid_at, payments.id
                        ROWS BETWEEN UNBOUNDED PRECEDING
                        AND 1 PRECEDING
                    ),
                    0
                ) AS previously_paid
            FROM prestamodesk_payments AS payments
            JOIN prestamodesk_installments AS installments
              ON installments.id = payments.installment_id
        )
        UPDATE prestamodesk_payments AS payments
        SET
            interest_amount = GREATEST(
                LEAST(
                    allocations.amount,
                    allocations.interest_due
                    - allocations.previously_paid
                ),
                0
            ),
            principal_amount = allocations.amount
                - GREATEST(
                    LEAST(
                        allocations.amount,
                        allocations.interest_due
                        - allocations.previously_paid
                    ),
                    0
                )
        FROM allocations
        WHERE allocations.id = payments.id
        """
    )


def downgrade() -> None:
    for column_name in (
        "late_fee_amount",
        "interest_amount",
        "principal_amount",
    ):
        op.drop_column(
            "prestamodesk_payments",
            column_name,
        )

    op.drop_column(
        "prestamodesk_installments",
        "late_fee_assessed_through",
    )

    for column_name in (
        "late_fee_paid",
        "late_fee_accrued",
        "interest_paid",
        "principal_paid",
    ):
        op.drop_column(
            "prestamodesk_installments",
            column_name,
        )

    op.drop_index(
        "ix_prestamodesk_late_fee_policies_tenant_id",
        table_name="prestamodesk_late_fee_policies",
    )
    op.drop_table(
        "prestamodesk_late_fee_policies"
    )

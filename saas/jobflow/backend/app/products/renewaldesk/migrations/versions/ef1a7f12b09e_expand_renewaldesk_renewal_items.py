"""Expand RenewalDesk renewal items

Revision ID: ef1a7f12b09e
Revises: 6d93e32da36a
Create Date: 2026-08-20 21:57:36.112852

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ef1a7f12b09e"
down_revision: Union[str, Sequence[str], None] = (
    "6d93e32da36a"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "renewaldesk_renewal_items",
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "renewaldesk_renewal_items",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "renewaldesk_renewal_items",
        sa.Column(
            "owner_name",
            sa.String(length=200),
            nullable=True,
        ),
    )

    op.add_column(
        "renewaldesk_renewal_items",
        sa.Column(
            "reminder_days",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "renewaldesk_renewal_items",
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "renewaldesk_renewal_items",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE renewaldesk_renewal_items
        SET
            category = COALESCE(
                category,
                'other'
            ),
            status = COALESCE(
                status,
                'active'
            ),
            reminder_days = COALESCE(
                reminder_days,
                30
            ),
            updated_at = COALESCE(
                updated_at,
                created_at
            )
        """
    )

    op.alter_column(
        "renewaldesk_renewal_items",
        "category",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    op.alter_column(
        "renewaldesk_renewal_items",
        "status",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    op.alter_column(
        "renewaldesk_renewal_items",
        "reminder_days",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "renewaldesk_renewal_items",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column(
        "renewaldesk_renewal_items",
        "updated_at",
    )

    op.drop_column(
        "renewaldesk_renewal_items",
        "notes",
    )

    op.drop_column(
        "renewaldesk_renewal_items",
        "reminder_days",
    )

    op.drop_column(
        "renewaldesk_renewal_items",
        "owner_name",
    )

    op.drop_column(
        "renewaldesk_renewal_items",
        "status",
    )

    op.drop_column(
        "renewaldesk_renewal_items",
        "category",
    )

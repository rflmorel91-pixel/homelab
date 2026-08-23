"""Add reminder occurrence identity

Revision ID: c6e9a3f4b012
Revises: b5d8f2e3a901
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6e9a3f4b012"
down_revision: Union[str, Sequence[str], None] = (
    "b5d8f2e3a901"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DELIVERY_TABLE = (
    "renewaldesk_reminder_deliveries"
)
ITEM_TABLE = "renewaldesk_renewal_items"
OCCURRENCE_CONSTRAINT = (
    "uq_renewaldesk_reminder_"
    "delivery_occurrence"
)


def upgrade() -> None:
    op.add_column(
        DELIVERY_TABLE,
        sa.Column(
            "occurrence_renewal_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        DELIVERY_TABLE,
        sa.Column(
            "reminder_days_snapshot",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            f"""
            UPDATE {DELIVERY_TABLE}
                AS deliveries
            SET
                occurrence_renewal_date =
                    items.renewal_date,
                reminder_days_snapshot =
                    items.reminder_days
            FROM {ITEM_TABLE} AS items
            WHERE
                items.id =
                    deliveries.renewal_item_id
            """
        )
    )

    op.alter_column(
        DELIVERY_TABLE,
        "occurrence_renewal_date",
        existing_type=sa.Date(),
        nullable=False,
    )

    op.alter_column(
        DELIVERY_TABLE,
        "reminder_days_snapshot",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_constraint(
        OCCURRENCE_CONSTRAINT,
        DELIVERY_TABLE,
        type_="unique",
    )

    op.create_unique_constraint(
        OCCURRENCE_CONSTRAINT,
        DELIVERY_TABLE,
        [
            "renewal_item_id",
            "channel",
            "occurrence_renewal_date",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        OCCURRENCE_CONSTRAINT,
        DELIVERY_TABLE,
        type_="unique",
    )

    op.create_unique_constraint(
        OCCURRENCE_CONSTRAINT,
        DELIVERY_TABLE,
        [
            "renewal_item_id",
            "channel",
            "scheduled_for",
        ],
    )

    op.drop_column(
        DELIVERY_TABLE,
        "reminder_days_snapshot",
    )

    op.drop_column(
        DELIVERY_TABLE,
        "occurrence_renewal_date",
    )

"""Expand RenewalDesk reminder delivery state

Revision ID: a4c7e1d2f890
Revises: 9e0f1a2b3c4d
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4c7e1d2f890"
down_revision: Union[str, Sequence[str], None] = (
    "9e0f1a2b3c4d"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE = "renewaldesk_reminder_deliveries"


def upgrade() -> None:
    op.add_column(
        TABLE,
        sa.Column(
            "recipient_email",
            sa.String(length=320),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "last_attempt_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "next_attempt_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "processing_started_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "last_error",
            sa.String(length=1000),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "provider_message_id",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "failed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_renewaldesk_reminder_delivery_status",
        TABLE,
        (
            "status IN ("
            "'pending', "
            "'processing', "
            "'retry_scheduled', "
            "'sent', "
            "'failed'"
            ")"
        ),
    )

    op.create_index(
        "ix_renewaldesk_reminder_delivery_due",
        TABLE,
        [
            "status",
            "next_attempt_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_renewaldesk_reminder_delivery_due",
        table_name=TABLE,
    )

    op.drop_constraint(
        "ck_renewaldesk_reminder_delivery_status",
        TABLE,
        type_="check",
    )

    op.drop_column(TABLE, "failed_at")
    op.drop_column(TABLE, "provider_message_id")
    op.drop_column(TABLE, "last_error")
    op.drop_column(TABLE, "processing_started_at")
    op.drop_column(TABLE, "next_attempt_at")
    op.drop_column(TABLE, "last_attempt_at")
    op.drop_column(TABLE, "attempt_count")
    op.drop_column(TABLE, "recipient_email")

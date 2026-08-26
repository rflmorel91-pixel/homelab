"""Add prospect outreach tracking.

Revision ID: b9c3e5f7d124
Revises: a8b2d4f6c013
Create Date: 2026-08-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9c3e5f7d124"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "a8b2d4f6c013"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


TABLE_NAME = (
    "workflow_automation_"
    "prospect_candidates"
)


def upgrade() -> None:
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "outreach_channel",
            sa.String(length=50),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "outreach_sent_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "follow_up_due_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "follow_up_completed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "reply_received_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "reply_outcome",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "operator_notes",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "suppressed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        TABLE_NAME,
        sa.Column(
            "suppression_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f(
            "ix_workflow_automation_"
            "prospect_candidates_"
            "follow_up_due_at"
        ),
        TABLE_NAME,
        ["follow_up_due_at"],
        unique=False,
    )
    op.create_index(
        op.f(
            "ix_workflow_automation_"
            "prospect_candidates_"
            "suppressed_at"
        ),
        TABLE_NAME,
        ["suppressed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_workflow_automation_"
            "prospect_candidates_"
            "suppressed_at"
        ),
        table_name=TABLE_NAME,
    )
    op.drop_index(
        op.f(
            "ix_workflow_automation_"
            "prospect_candidates_"
            "follow_up_due_at"
        ),
        table_name=TABLE_NAME,
    )

    for column_name in (
        "suppression_reason",
        "suppressed_at",
        "operator_notes",
        "reply_outcome",
        "reply_received_at",
        "follow_up_completed_at",
        "follow_up_due_at",
        "outreach_sent_at",
        "outreach_channel",
    ):
        op.drop_column(
            TABLE_NAME,
            column_name,
        )

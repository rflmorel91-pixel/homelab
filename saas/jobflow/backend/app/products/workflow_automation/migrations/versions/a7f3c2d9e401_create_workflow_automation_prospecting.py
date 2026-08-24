"""Create Workflow Automation prospecting

Revision ID: a7f3c2d9e401
Revises: c6e9a3f4b012
Create Date: 2026-08-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7f3c2d9e401"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "c6e9a3f4b012"

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


def upgrade() -> None:
    op.create_table(
        "workflow_automation_"
        "prospecting_campaigns",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "geography",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "segments",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "max_candidates",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "minimum_score",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "model",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f(
            "ix_workflow_automation_"
            "prospecting_campaigns_status"
        ),
        "workflow_automation_"
        "prospecting_campaigns",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_workflow_automation_"
            "prospecting_campaigns_"
            "created_by_user_id"
        ),
        "workflow_automation_"
        "prospecting_campaigns",
        ["created_by_user_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_workflow_automation_"
            "prospecting_campaigns_created_at"
        ),
        "workflow_automation_"
        "prospecting_campaigns",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "workflow_automation_"
        "prospect_candidates",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "lead_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "business_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "website_url",
            sa.String(length=1000),
            nullable=False,
        ),
        sa.Column(
            "normalized_domain",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "segment",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "location",
            sa.String(length=300),
            nullable=False,
        ),
        sa.Column(
            "contact_name",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "phone",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "evidence",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "fit_score",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "score_reasons",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "disqualifiers",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "outreach_subject",
            sa.String(length=300),
            nullable=False,
        ),
        sa.Column(
            "outreach_body",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "review_status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
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
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            [
                "workflow_automation_"
                "prospecting_campaigns.id"
            ],
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for column in (
        "campaign_id",
        "lead_id",
        "normalized_domain",
        "segment",
        "email",
        "review_status",
        "reviewed_by_user_id",
        "created_at",
    ):
        op.create_index(
            op.f(
                "ix_workflow_automation_"
                "prospect_candidates_"
                f"{column}"
            ),
            "workflow_automation_"
            "prospect_candidates",
            [column],
            unique=(
                column in {
                    "lead_id",
                    "normalized_domain",
                }
            ),
        )


def downgrade() -> None:
    for column in (
        "created_at",
        "reviewed_by_user_id",
        "review_status",
        "email",
        "segment",
        "normalized_domain",
        "lead_id",
        "campaign_id",
    ):
        op.drop_index(
            op.f(
                "ix_workflow_automation_"
                "prospect_candidates_"
                f"{column}"
            ),
            table_name=(
                "workflow_automation_"
                "prospect_candidates"
            ),
        )

    op.drop_table(
        "workflow_automation_"
        "prospect_candidates"
    )

    op.drop_index(
        op.f(
            "ix_workflow_automation_"
            "prospecting_campaigns_created_at"
        ),
        table_name=(
            "workflow_automation_"
            "prospecting_campaigns"
        ),
    )

    op.drop_index(
        op.f(
            "ix_workflow_automation_"
            "prospecting_campaigns_"
            "created_by_user_id"
        ),
        table_name=(
            "workflow_automation_"
            "prospecting_campaigns"
        ),
    )

    op.drop_index(
        op.f(
            "ix_workflow_automation_"
            "prospecting_campaigns_status"
        ),
        table_name=(
            "workflow_automation_"
            "prospecting_campaigns"
        ),
    )

    op.drop_table(
        "workflow_automation_"
        "prospecting_campaigns"
    )

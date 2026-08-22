"""Link user invitations to leads

Revision ID: 6b7c8d9e0f1a
Revises: 1ad372a7da0d
Create Date: 2026-08-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6b7c8d9e0f1a"
down_revision: Union[str, Sequence[str], None] = "1ad372a7da0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_invitations",
        sa.Column(
            "lead_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    invitation_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM user_invitations
            """
        )
    ).scalar_one()

    if invitation_count != 0:
        raise RuntimeError(
            "Existing user invitations must be resolved "
            "before requiring lead ownership"
        )

    op.alter_column(
        "user_invitations",
        "lead_id",
        nullable=False,
    )

    op.create_index(
        op.f("ix_user_invitations_lead_id"),
        "user_invitations",
        ["lead_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_user_invitations_lead_id_leads",
        "user_invitations",
        "leads",
        ["lead_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_user_invitations_lead_id_leads",
        "user_invitations",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_user_invitations_lead_id"),
        table_name="user_invitations",
    )

    op.drop_column(
        "user_invitations",
        "lead_id",
    )

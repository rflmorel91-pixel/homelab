"""add user invitations

Revision ID: 1ad372a7da0d
Revises: 385d6260b08a
Create Date: 2026-08-22 15:39:44.426610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1ad372a7da0d"
down_revision: Union[str, Sequence[str], None] = "385d6260b08a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_invitations",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "accepted_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "accepted_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["accepted_user_id"],
            ["users.id"],
            name=(
                "fk_user_invitations_"
                "accepted_user_id_users"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=(
                "fk_user_invitations_"
                "created_by_user_id_users"
            ),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_user_invitations_email"),
        "user_invitations",
        ["email"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_invitations_token_hash"),
        "user_invitations",
        ["token_hash"],
        unique=True,
    )

    op.create_index(
        op.f("ix_user_invitations_created_by_user_id"),
        "user_invitations",
        ["created_by_user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_invitations_accepted_user_id"),
        "user_invitations",
        ["accepted_user_id"],
        unique=True,
    )

    op.create_index(
        op.f("ix_user_invitations_expires_at"),
        "user_invitations",
        ["expires_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_invitations_created_at"),
        "user_invitations",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_invitations_created_at"),
        table_name="user_invitations",
    )

    op.drop_index(
        op.f("ix_user_invitations_expires_at"),
        table_name="user_invitations",
    )

    op.drop_index(
        op.f("ix_user_invitations_accepted_user_id"),
        table_name="user_invitations",
    )

    op.drop_index(
        op.f("ix_user_invitations_created_by_user_id"),
        table_name="user_invitations",
    )

    op.drop_index(
        op.f("ix_user_invitations_token_hash"),
        table_name="user_invitations",
    )

    op.drop_index(
        op.f("ix_user_invitations_email"),
        table_name="user_invitations",
    )

    op.drop_table("user_invitations")

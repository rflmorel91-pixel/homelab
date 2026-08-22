"""Support client user invitations

Revision ID: 8d9e0f1a2b3c
Revises: 7c8d9e0f1a2b
Create Date: 2026-08-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8d9e0f1a2b3c"
down_revision: Union[str, Sequence[str], None] = "7c8d9e0f1a2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_invitations",
        sa.Column(
            "tenant_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "user_invitations",
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.alter_column(
        "user_invitations",
        "lead_id",
        nullable=True,
    )

    op.create_index(
        op.f("ix_user_invitations_tenant_id"),
        "user_invitations",
        ["tenant_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_user_invitations_tenant_id_tenants",
        "user_invitations",
        "tenants",
        ["tenant_id"],
        ["id"],
    )

    op.create_check_constraint(
        "ck_user_invitations_single_target",
        "user_invitations",
        """
        (
            lead_id IS NOT NULL
            AND tenant_id IS NULL
            AND role IS NULL
        )
        OR
        (
            lead_id IS NULL
            AND tenant_id IS NOT NULL
            AND role IN ('owner', 'member')
        )
        """,
    )


def downgrade() -> None:
    connection = op.get_bind()

    client_invitation_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM user_invitations
            WHERE tenant_id IS NOT NULL
            """
        )
    ).scalar_one()

    if client_invitation_count != 0:
        raise RuntimeError(
            "Client invitations must be reconciled "
            "before downgrading"
        )

    op.drop_constraint(
        "ck_user_invitations_single_target",
        "user_invitations",
        type_="check",
    )

    op.drop_constraint(
        "fk_user_invitations_tenant_id_tenants",
        "user_invitations",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_user_invitations_tenant_id"),
        table_name="user_invitations",
    )

    op.alter_column(
        "user_invitations",
        "lead_id",
        nullable=False,
    )

    op.drop_column(
        "user_invitations",
        "role",
    )

    op.drop_column(
        "user_invitations",
        "tenant_id",
    )

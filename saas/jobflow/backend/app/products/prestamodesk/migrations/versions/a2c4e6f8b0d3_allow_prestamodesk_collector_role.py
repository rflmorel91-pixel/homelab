"""allow prestamodesk collector role

Revision ID: a2c4e6f8b0d3
Revises: f1c3e5a7b9d2
Create Date: 2026-10-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a2c4e6f8b0d3"
down_revision: str | None = "f1c3e5a7b9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


OLD_CONSTRAINT = """
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
"""


NEW_CONSTRAINT = """
(
    lead_id IS NOT NULL
    AND tenant_id IS NULL
    AND role IS NULL
)
OR
(
    lead_id IS NULL
    AND tenant_id IS NOT NULL
    AND role IN ('owner', 'member', 'collector')
)
"""


def upgrade() -> None:
    op.drop_constraint(
        "ck_user_invitations_single_target",
        "user_invitations",
        type_="check",
    )
    op.create_check_constraint(
        "ck_user_invitations_single_target",
        "user_invitations",
        NEW_CONSTRAINT,
    )


def downgrade() -> None:
    connection = op.get_bind()

    collector_invitation_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM user_invitations
            WHERE role = 'collector'
            """
        )
    ).scalar_one()

    if collector_invitation_count != 0:
        raise RuntimeError(
            "Collector invitations must be reconciled "
            "before downgrading"
        )

    op.drop_constraint(
        "ck_user_invitations_single_target",
        "user_invitations",
        type_="check",
    )
    op.create_check_constraint(
        "ck_user_invitations_single_target",
        "user_invitations",
        OLD_CONSTRAINT,
    )

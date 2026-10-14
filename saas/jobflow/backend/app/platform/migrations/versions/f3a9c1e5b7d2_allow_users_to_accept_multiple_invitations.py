"""Allow one user to accept multiple invitations."""

from collections.abc import Sequence
from typing import Union

from alembic import op


revision: str = "f3a9c1e5b7d2"
down_revision: Union[str, Sequence[str], None] = "d4f6a8c0e2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_user_invitations_accepted_user_id",
        table_name="user_invitations",
    )
    op.create_index(
        "ix_user_invitations_accepted_user_id",
        "user_invitations",
        ["accepted_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_invitations_accepted_user_id",
        table_name="user_invitations",
    )
    op.create_index(
        "ix_user_invitations_accepted_user_id",
        "user_invitations",
        ["accepted_user_id"],
        unique=True,
    )

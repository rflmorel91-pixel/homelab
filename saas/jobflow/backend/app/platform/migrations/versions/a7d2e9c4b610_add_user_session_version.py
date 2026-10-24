"""Add account session versions for password-reset revocation."""

from alembic import op
import sqlalchemy as sa

revision = "a7d2e9c4b610"
down_revision = "f3a9c1e5b7d2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "session_version",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("users", "session_version")

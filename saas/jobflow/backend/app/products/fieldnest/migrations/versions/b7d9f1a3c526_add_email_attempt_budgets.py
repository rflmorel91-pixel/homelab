"""Persist FieldNest email attempt budgets across API workers and restarts."""
from alembic import op
import sqlalchemy as sa

revision = "b7d9f1a3c526"
down_revision = "a6c8e0f2b415"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fieldnest_email_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("notification_id", sa.Integer(), nullable=False),
        sa.Column("recipient_hash", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fieldnest_email_attempts_attempted_at", "fieldnest_email_attempts", ["attempted_at"])
    op.create_index("ix_fieldnest_email_attempts_tenant_time", "fieldnest_email_attempts", ["tenant_id", "attempted_at"])
    op.create_index("ix_fieldnest_email_attempts_recipient_time", "fieldnest_email_attempts", ["recipient_hash", "attempted_at"])


def downgrade():
    op.drop_table("fieldnest_email_attempts")

"""Add the FieldNest maintenance email outbox."""
from alembic import op
import sqlalchemy as sa

revision = "e4b6d8f0a213"
down_revision = "f2a4c6e8b091"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fieldnest_notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("fieldnest_work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("receipt_email", sa.String(254), nullable=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("event_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(80), nullable=True),
    )
    for column in ["tenant_id", "work_order_id", "status", "available_at"]:
        op.create_index(f"ix_fieldnest_notifications_{column}", "fieldnest_notifications", [column])
    op.create_index("ix_fieldnest_notifications_event_key", "fieldnest_notifications", ["event_key"], unique=True)


def downgrade():
    op.drop_table("fieldnest_notifications")

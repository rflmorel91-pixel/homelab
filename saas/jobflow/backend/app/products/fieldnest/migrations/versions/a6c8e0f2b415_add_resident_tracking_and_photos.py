"""Private resident request tracking and bounded photo storage."""
from alembic import op
import sqlalchemy as sa
revision = "a6c8e0f2b415"
down_revision = "e4b6d8f0a213"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("fieldnest_work_orders", sa.Column("tracking_token_hash", sa.String(64), nullable=True))
    op.add_column("fieldnest_work_orders", sa.Column("tracking_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_fieldnest_work_orders_tracking_token_hash", "fieldnest_work_orders", ["tracking_token_hash"], unique=True)
    op.create_table("fieldnest_photos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("fieldnest_work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_fieldnest_photos_tenant_id", "fieldnest_photos", ["tenant_id"])
    op.create_index("ix_fieldnest_photos_work_order_id", "fieldnest_photos", ["work_order_id"])


def downgrade():
    op.drop_table("fieldnest_photos")
    op.drop_index("ix_fieldnest_work_orders_tracking_token_hash", table_name="fieldnest_work_orders")
    op.drop_column("fieldnest_work_orders", "tracking_token_expires_at")
    op.drop_column("fieldnest_work_orders", "tracking_token_hash")

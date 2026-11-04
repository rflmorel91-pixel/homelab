"""Add revocable property request links and anonymous work-order intake."""
from alembic import op
import sqlalchemy as sa

revision = "f2a4c6e8b091"
down_revision = "9c71f4a2d630"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("fieldnest_properties", sa.Column("request_token_hash", sa.String(64), nullable=True))
    op.add_column("fieldnest_properties", sa.Column("request_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_fieldnest_properties_request_token_hash", "fieldnest_properties", ["request_token_hash"], unique=True)
    op.alter_column("fieldnest_work_orders", "created_by_user_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("fieldnest_work_orders", sa.Column("intake_key", sa.String(36), nullable=True))
    op.create_index("ix_fieldnest_work_orders_intake_key", "fieldnest_work_orders", ["intake_key"], unique=True)


def downgrade():
    # Restoring NOT NULL requires explicit attribution of any resident reports.
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT count(*) FROM fieldnest_work_orders WHERE created_by_user_id IS NULL")).scalar():
        raise RuntimeError("Attribute resident reports to a valid user before downgrading; no rows were deleted.")
    op.drop_index("ix_fieldnest_work_orders_intake_key", table_name="fieldnest_work_orders")
    op.drop_column("fieldnest_work_orders", "intake_key")
    op.alter_column("fieldnest_work_orders", "created_by_user_id", existing_type=sa.Integer(), nullable=False)
    op.drop_index("ix_fieldnest_properties_request_token_hash", table_name="fieldnest_properties")
    op.drop_column("fieldnest_properties", "request_token_expires_at")
    op.drop_column("fieldnest_properties", "request_token_hash")

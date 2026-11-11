"""Add tenant-scoped maintenance plans and durable work-order occurrences."""
from alembic import op
import sqlalchemy as sa

revision = "c8e0a2b4d637"
down_revision = "b7d9f1a3c526"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fieldnest_maintenance_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("fieldnest_properties.id"), nullable=False),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("fieldnest_vendors.id")),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("interval_months", sa.Integer(), nullable=False),
        sa.Column("anchor_day", sa.Integer(), nullable=False),
        sa.Column("next_due", sa.Date(), nullable=False),
        sa.Column("paused", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("interval_months IN (1, 3, 6, 12)", name="ck_fieldnest_plan_interval"),
    )
    op.create_index("ix_fieldnest_maintenance_plans_tenant_id", "fieldnest_maintenance_plans", ["tenant_id"])
    op.create_table(
        "fieldnest_maintenance_occurrences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("fieldnest_maintenance_plans.id"), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("fieldnest_work_orders.id"), nullable=False, unique=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("plan_id", "scheduled_date", name="uq_fieldnest_plan_date"),
    )
    op.create_index("ix_fieldnest_maintenance_occurrences_tenant_id", "fieldnest_maintenance_occurrences", ["tenant_id"])


def downgrade():
    # Occurrence links are business history. Require an explicit data decision.
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM fieldnest_maintenance_plans LIMIT 1")).first():
        raise RuntimeError("Maintenance plans exist; export and explicitly resolve their history before downgrade")
    op.drop_table("fieldnest_maintenance_occurrences")
    op.drop_table("fieldnest_maintenance_plans")

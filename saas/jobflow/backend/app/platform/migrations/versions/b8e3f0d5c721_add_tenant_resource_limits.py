"""Add optional per-tenant resource limits without assigning any plans."""

from alembic import op
import sqlalchemy as sa

revision = "b8e3f0d5c721"
down_revision = "a7d2e9c4b610"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "platform_tenant_resource_limits",
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("resource_key", sa.String(100), nullable=False),
        sa.Column("maximum_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "maximum_count >= 0",
            name="ck_platform_tenant_resource_limits_nonnegative",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("tenant_id", "resource_key"),
    )


def downgrade():
    op.drop_table("platform_tenant_resource_limits")

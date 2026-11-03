"""Create FieldNest property operations tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c71f4a2d630"
down_revision: Union[str, Sequence[str], None] = "b8e3f0d5c721"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fieldnest_properties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("address", sa.String(300), nullable=False),
        sa.Column("property_type", sa.String(40), nullable=False, server_default="residential"),
        sa.Column("total_units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fieldnest_properties_tenant_id", "fieldnest_properties", ["tenant_id"])

    op.create_table(
        "fieldnest_residents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("fieldnest_properties.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("unit", sa.String(60), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fieldnest_residents_tenant_id", "fieldnest_residents", ["tenant_id"])
    op.create_index("ix_fieldnest_residents_property_id", "fieldnest_residents", ["property_id"])

    op.create_table(
        "fieldnest_vendors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("trade", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(60), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("insurance_expires", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fieldnest_vendors_tenant_id", "fieldnest_vendors", ["tenant_id"])

    op.create_table(
        "fieldnest_work_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("fieldnest_properties.id"), nullable=False),
        sa.Column("resident_id", sa.Integer(), sa.ForeignKey("fieldnest_residents.id"), nullable=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("fieldnest_vendors.id"), nullable=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("unit", sa.String(80), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(24), nullable=False, server_default="open"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fieldnest_work_orders_tenant_id", "fieldnest_work_orders", ["tenant_id"])
    op.create_index("ix_fieldnest_work_orders_property_id", "fieldnest_work_orders", ["property_id"])
    op.create_index("ix_fieldnest_work_orders_resident_id", "fieldnest_work_orders", ["resident_id"])
    op.create_index("ix_fieldnest_work_orders_vendor_id", "fieldnest_work_orders", ["vendor_id"])


def downgrade() -> None:
    op.drop_table("fieldnest_work_orders")
    op.drop_table("fieldnest_vendors")
    op.drop_table("fieldnest_residents")
    op.drop_table("fieldnest_properties")

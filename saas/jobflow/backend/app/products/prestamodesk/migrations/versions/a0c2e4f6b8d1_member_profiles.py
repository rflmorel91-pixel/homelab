"""Business-scoped member contact profiles.
Revision ID: a0c2e4f6b8d1
Revises: f9b1d3e5a7c0
"""
from alembic import op
import sqlalchemy as sa

revision = "a0c2e4f6b8d1"
down_revision = "f9b1d3e5a7c0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("prestamodesk_member_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("membership_id", sa.Integer(), sa.ForeignKey("tenant_memberships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("correspondence_email", sa.String(320), nullable=True),
        sa.Column("preferred_contact", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("membership_id"))
    op.create_index("ix_prestamodesk_member_profiles_tenant_id", "prestamodesk_member_profiles", ["tenant_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM prestamodesk_member_profiles")).scalar_one():
        raise RuntimeError("Export and reconcile member profiles before downgrade; contact records cannot be discarded")
    op.drop_index("ix_prestamodesk_member_profiles_tenant_id", table_name="prestamodesk_member_profiles")
    op.drop_table("prestamodesk_member_profiles")

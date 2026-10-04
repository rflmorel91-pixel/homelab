"""PréstamoDesk administration roles and tenant membership suspension.

Revision ID: d7f9a1c3e5b8
Revises: c6e8a0b2d4f7
"""
from alembic import op
import sqlalchemy as sa

revision = "d7f9a1c3e5b8"
down_revision = "c6e8a0b2d4f7"
branch_labels = None
depends_on = None

OLD = """(lead_id IS NOT NULL AND tenant_id IS NULL AND role IS NULL)
OR (lead_id IS NULL AND tenant_id IS NOT NULL AND role IN ('owner', 'member', 'collector'))"""
NEW = """(lead_id IS NOT NULL AND tenant_id IS NULL AND role IS NULL)
OR (lead_id IS NULL AND tenant_id IS NOT NULL AND role IN
('owner', 'member', 'collector', 'administrator', 'supervisor', 'cashier'))"""


def upgrade():
    op.add_column("tenant_memberships", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    with op.batch_alter_table("user_invitations") as batch:
        batch.drop_constraint("ck_user_invitations_single_target", type_="check")
        batch.create_check_constraint("ck_user_invitations_single_target", NEW)


def downgrade():
    connection = op.get_bind()
    count = connection.execute(sa.text("""SELECT
        (SELECT COUNT(*) FROM user_invitations WHERE role IN ('administrator', 'supervisor', 'cashier')) +
        (SELECT COUNT(*) FROM tenant_memberships WHERE role IN ('administrator', 'supervisor', 'cashier') OR NOT is_active)
    """)).scalar_one()
    if count:
        raise RuntimeError("Reconcile administration roles and suspended memberships before downgrading")
    with op.batch_alter_table("user_invitations") as batch:
        batch.drop_constraint("ck_user_invitations_single_target", type_="check")
        batch.create_check_constraint("ck_user_invitations_single_target", OLD)
    op.drop_column("tenant_memberships", "is_active")

"""Snapshot-backed payment voids without deleting financial history.

Revision ID: e8a0c2d4f6b9
Revises: d7f9a1c3e5b8
"""
from alembic import op
import sqlalchemy as sa

revision = "e8a0c2d4f6b9"
down_revision = "d7f9a1c3e5b8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("prestamodesk_payments") as batch:
        batch.add_column(sa.Column("correction_snapshot", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("voided_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("voided_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("void_reason", sa.Text(), nullable=True))
        batch.create_foreign_key("fk_prestamodesk_payment_void_user", "users", ["voided_by_user_id"], ["id"])
        batch.create_check_constraint("ck_prestamodesk_payment_void",
            "(voided_at IS NULL AND voided_by_user_id IS NULL AND void_reason IS NULL) OR "
            "(voided_at IS NOT NULL AND voided_by_user_id IS NOT NULL AND void_reason IS NOT NULL)")
    op.add_column("prestamodesk_promise_payment_allocations", sa.Column("reversed_at", sa.DateTime(), nullable=True))


def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT COUNT(*) FROM prestamodesk_payments WHERE voided_at IS NOT NULL")).scalar_one():
        raise RuntimeError("Reconcile voided payments before downgrading; financial history cannot be discarded")
    op.drop_column("prestamodesk_promise_payment_allocations", "reversed_at")
    with op.batch_alter_table("prestamodesk_payments") as batch:
        batch.drop_constraint("ck_prestamodesk_payment_void", type_="check")
        batch.drop_constraint("fk_prestamodesk_payment_void_user", type_="foreignkey")
        for column in ("void_reason", "voided_by_user_id", "voided_at", "correction_snapshot"):
            batch.drop_column(column)

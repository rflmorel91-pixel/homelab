"""Retain atomic loan creation requests and initial schedules."""
from alembic import op
import sqlalchemy as sa
revision = "c2d4e6f8a0b2"
down_revision = "b1d3f5a7c9e2"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("prestamodesk_loans") as batch:
        batch.add_column(sa.Column("idempotency_key", sa.String(36), nullable=True))
        batch.add_column(sa.Column("request_fingerprint", sa.String(64), nullable=True))
        batch.add_column(sa.Column("created_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("creation_snapshot", sa.JSON(), nullable=True))
        batch.create_foreign_key("fk_prestamodesk_loan_creator", "users", ["created_by_user_id"], ["id"])
        batch.create_unique_constraint("uq_prestamodesk_loan_request", ["tenant_id", "idempotency_key"])

def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM prestamodesk_loans WHERE idempotency_key IS NOT NULL")).scalar_one():
        raise RuntimeError("Loan request history must be retained; downgrade would remove retry protection")
    with op.batch_alter_table("prestamodesk_loans") as batch:
        batch.drop_constraint("uq_prestamodesk_loan_request", type_="unique")
        batch.drop_constraint("fk_prestamodesk_loan_creator", type_="foreignkey")
        for name in ("creation_snapshot", "created_by_user_id", "request_fingerprint", "idempotency_key"):
            batch.drop_column(name)

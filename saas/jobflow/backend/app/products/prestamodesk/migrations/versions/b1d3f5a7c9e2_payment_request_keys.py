"""Store unique payment requests and original receipt snapshots."""
from alembic import op
import sqlalchemy as sa
revision = "b1d3f5a7c9e2"
down_revision = "a0c2e4f6b8d1"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("prestamodesk_payments") as batch:
        batch.add_column(sa.Column("idempotency_key", sa.String(36), nullable=True))
        batch.add_column(sa.Column("request_fingerprint", sa.String(64), nullable=True))
        batch.add_column(sa.Column("receipt_snapshot", sa.JSON(), nullable=True))
        batch.create_unique_constraint("uq_prestamodesk_payment_request", ["tenant_id", "idempotency_key"])

def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT COUNT(*) FROM prestamodesk_payments WHERE idempotency_key IS NOT NULL")).scalar_one():
        raise RuntimeError("Payment request history must be retained; downgrade would remove retry protection")
    with op.batch_alter_table("prestamodesk_payments") as batch:
        batch.drop_constraint("uq_prestamodesk_payment_request", type_="unique")
        for name in ("receipt_snapshot", "request_fingerprint", "idempotency_key"):
            batch.drop_column(name)

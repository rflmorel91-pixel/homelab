"""Preserve portfolio opening balances and prevent repeated imports."""
from alembic import op
import sqlalchemy as sa

revision = "c2e4f6a8b0d3"
down_revision = "b1d3f5a7c9e2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("prestamodesk_portfolio_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("cutoff_date", sa.Date(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "fingerprint", name="uq_prestamodesk_import_fingerprint"))
    op.create_index("ix_prestamodesk_portfolio_imports_tenant_id", "prestamodesk_portfolio_imports", ["tenant_id"])
    op.create_table("prestamodesk_imported_loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("import_id", sa.Integer(), sa.ForeignKey("prestamodesk_portfolio_imports.id"), nullable=False),
        sa.Column("loan_id", sa.Integer(), sa.ForeignKey("prestamodesk_loans.id"), nullable=False),
        sa.Column("external_reference", sa.String(100), nullable=False),
        sa.UniqueConstraint("tenant_id", "external_reference", name="uq_prestamodesk_import_reference"))
    op.create_index("ix_prestamodesk_imported_loans_tenant_id", "prestamodesk_imported_loans", ["tenant_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM prestamodesk_portfolio_imports")).scalar_one():
        raise RuntimeError("Retain opening-balance history before downgrading")
    op.drop_table("prestamodesk_imported_loans")
    op.drop_table("prestamodesk_portfolio_imports")

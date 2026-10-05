"""Link prospects to applications and support personal application terms.

Revision ID: f9b1d3e5a7c0
Revises: e8a0c2d4f6b9
"""
from alembic import op
import sqlalchemy as sa

revision = "f9b1d3e5a7c0"
down_revision = "e8a0c2d4f6b9"
branch_labels = None
depends_on = None

VEHICLE_COLUMNS = {
    "vehicle_cash_price": sa.Numeric(14, 2),
    "vehicle_down_payment": sa.Numeric(14, 2),
    "vehicle_make": sa.String(100),
    "vehicle_model": sa.String(100),
    "vehicle_year": sa.Integer(),
}


def upgrade():
    with op.batch_alter_table("prestamodesk_applications") as batch:
        batch.add_column(sa.Column("source_prospect_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_prestamodesk_application_prospect", "prestamodesk_prospects", ["source_prospect_id"], ["id"])
        batch.create_unique_constraint("uq_prestamodesk_application_prospect", ["source_prospect_id"])
        for name, column_type in VEHICLE_COLUMNS.items():
            batch.alter_column(name, existing_type=column_type, existing_nullable=False, nullable=True)


def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text(
        "SELECT COUNT(*) FROM prestamodesk_applications WHERE "
        "source_prospect_id IS NOT NULL OR loan_type = 'personal' OR "
        + " OR ".join(f"{name} IS NULL" for name in VEHICLE_COLUMNS)
    )).scalar_one():
        raise RuntimeError("Reconcile prospect-linked and personal applications before downgrade; application history cannot be discarded")
    with op.batch_alter_table("prestamodesk_applications") as batch:
        for name, column_type in VEHICLE_COLUMNS.items():
            batch.alter_column(name, existing_type=column_type, existing_nullable=True, nullable=False)
        batch.drop_constraint("uq_prestamodesk_application_prospect", type_="unique")
        batch.drop_constraint("fk_prestamodesk_application_prospect", type_="foreignkey")
        batch.drop_column("source_prospect_id")

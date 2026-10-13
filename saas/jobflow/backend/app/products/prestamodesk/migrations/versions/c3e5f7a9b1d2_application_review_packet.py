"""Add tenant-scoped application review packets and decision history."""

from alembic import op
import sqlalchemy as sa


revision = "c3e5f7a9b1d2"
down_revision = "c2d4e6f8a0b2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("prestamodesk_applications") as batch:
        batch.add_column(sa.Column("decision_reason", sa.Text(), nullable=True))

    op.create_table(
        "prestamodesk_application_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "application_id", sa.Integer(),
            sa.ForeignKey("prestamodesk_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id", sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("packet", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("application_id", name="uq_prestamodesk_application_review_application"),
    )
    op.create_index(
        "ix_prestamodesk_application_reviews_application_id",
        "prestamodesk_application_reviews", ["application_id"],
    )
    op.create_index(
        "ix_prestamodesk_application_reviews_tenant_id",
        "prestamodesk_application_reviews", ["tenant_id"],
    )

    op.create_table(
        "prestamodesk_application_review_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "application_id", sa.Integer(),
            sa.ForeignKey("prestamodesk_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id", sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_prestamodesk_application_review_events_application_id",
        "prestamodesk_application_review_events", ["application_id"],
    )
    op.create_index(
        "ix_prestamodesk_application_review_events_tenant_id",
        "prestamodesk_application_review_events", ["tenant_id"],
    )


def downgrade():
    op.drop_index(
        "ix_prestamodesk_application_review_events_tenant_id",
        table_name="prestamodesk_application_review_events",
    )
    op.drop_index(
        "ix_prestamodesk_application_review_events_application_id",
        table_name="prestamodesk_application_review_events",
    )
    op.drop_table("prestamodesk_application_review_events")
    op.drop_index(
        "ix_prestamodesk_application_reviews_tenant_id",
        table_name="prestamodesk_application_reviews",
    )
    op.drop_index(
        "ix_prestamodesk_application_reviews_application_id",
        table_name="prestamodesk_application_reviews",
    )
    op.drop_table("prestamodesk_application_reviews")
    with op.batch_alter_table("prestamodesk_applications") as batch:
        batch.drop_column("decision_reason")

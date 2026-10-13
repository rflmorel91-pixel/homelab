"""Track tenant-scoped metadata for private PrestamoDesk review documents."""

from alembic import op
import sqlalchemy as sa


revision = "d4f6a8c0e2b4"
down_revision = "c3e5f7a9b1d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prestamodesk_application_review_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("storage_ref", sa.String(length=36), nullable=False),
        sa.Column(
            "tenant_id", sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "application_id", sa.Integer(),
            sa.ForeignKey("prestamodesk_applications.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("document_type", sa.String(length=40), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("file_key", sa.String(length=240), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("file_key", name="uq_prestamodesk_review_document_file_key"),
    )
    op.create_index(
        "ix_prestamodesk_application_review_documents_storage_ref",
        "prestamodesk_application_review_documents", ["storage_ref"], unique=True,
    )
    op.create_index(
        "ix_prestamodesk_application_review_documents_tenant_id",
        "prestamodesk_application_review_documents", ["tenant_id"],
    )
    op.create_index(
        "ix_prestamodesk_application_review_documents_application_id",
        "prestamodesk_application_review_documents", ["application_id"],
    )


def downgrade():
    op.drop_index(
        "ix_prestamodesk_application_review_documents_application_id",
        table_name="prestamodesk_application_review_documents",
    )
    op.drop_index(
        "ix_prestamodesk_application_review_documents_tenant_id",
        table_name="prestamodesk_application_review_documents",
    )
    op.drop_index(
        "ix_prestamodesk_application_review_documents_storage_ref",
        table_name="prestamodesk_application_review_documents",
    )
    op.drop_table("prestamodesk_application_review_documents")

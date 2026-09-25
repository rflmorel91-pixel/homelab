"""Create PréstamoDesk borrowers

Revision ID: 8d9e1f2a3b4c
Revises: 4b94903229c6
Create Date: 2026-09-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8d9e1f2a3b4c"
down_revision: Union[str, Sequence[str], None] = "4b94903229c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_borrowers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("document_number", sa.String(length=50), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("municipality", sa.String(length=120), nullable=True),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "document_number",
            name="uq_prestamodesk_borrower_tenant_document",
        ),
    )

    op.create_index(
        op.f("ix_prestamodesk_borrowers_tenant_id"),
        "prestamodesk_borrowers",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_prestamodesk_borrowers_tenant_id"),
        table_name="prestamodesk_borrowers",
    )
    op.drop_table("prestamodesk_borrowers")

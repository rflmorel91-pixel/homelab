"""Create PréstamoDesk prospects

Revision ID: 7c9e1a3b5d6f
Revises: 5a7c9e1f3b2d
Create Date: 2026-09-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c9e1a3b5d6f"
down_revision: Union[str, Sequence[str], None] = (
    "5a7c9e1f3b2d"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_prospects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "converted_borrower_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "full_name",
            sa.String(200),
            nullable=False,
        ),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column(
            "municipality",
            sa.String(120),
            nullable=True,
        ),
        sa.Column(
            "province",
            sa.String(120),
            nullable=True,
        ),
        sa.Column(
            "requested_amount",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "preferred_contact",
            sa.String(30),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
        ),
        sa.Column(
            "consented_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "consent_notice_version",
            sa.String(30),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["converted_borrower_id"],
            ["prestamodesk_borrowers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("converted_borrower_id"),
    )

    for column in (
        "tenant_id",
        "status",
        "created_at",
    ):
        op.create_index(
            op.f(
                f"ix_prestamodesk_prospects_{column}"
            ),
            "prestamodesk_prospects",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in (
        "created_at",
        "status",
        "tenant_id",
    ):
        op.drop_index(
            op.f(
                f"ix_prestamodesk_prospects_{column}"
            ),
            table_name="prestamodesk_prospects",
        )

    op.drop_table("prestamodesk_prospects")

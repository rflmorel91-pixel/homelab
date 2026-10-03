"""create prestamodesk collector assignments

Revision ID: c6e8a0b2d4f7
Revises: b3d5f7a9c1e4
Create Date: 2026-10-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c6e8a0b2d4f7"
down_revision: str | None = "b3d5f7a9c1e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prestamodesk_loan_collector_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column(
            "collector_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "assigned_by_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "assigned_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "released_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "released_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "release_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.CheckConstraint(
            "("
            "released_at IS NULL "
            "AND released_by_user_id IS NULL"
            ") OR ("
            "released_at IS NOT NULL "
            "AND released_by_user_id IS NOT NULL"
            ")",
            name=(
                "ck_prestamodesk_collector_assignment_release"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["loan_id"],
            ["prestamodesk_loans.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["collector_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["released_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for column in (
        "tenant_id",
        "loan_id",
        "collector_user_id",
        "assigned_by_user_id",
        "assigned_at",
        "released_at",
        "released_by_user_id",
    ):
        op.create_index(
            (
                "ix_prestamodesk_loan_collector_"
                "assignments_" + column
            ),
            "prestamodesk_loan_collector_assignments",
            [column],
        )

    op.create_index(
        "uq_prestamodesk_active_collector_assignment",
        "prestamodesk_loan_collector_assignments",
        ["tenant_id", "loan_id"],
        unique=True,
        postgresql_where=sa.text(
            "released_at IS NULL"
        ),
        sqlite_where=sa.text(
            "released_at IS NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_prestamodesk_active_collector_assignment",
        table_name=(
            "prestamodesk_loan_collector_assignments"
        ),
    )

    for column in (
        "released_by_user_id",
        "released_at",
        "assigned_at",
        "assigned_by_user_id",
        "collector_user_id",
        "loan_id",
        "tenant_id",
    ):
        op.drop_index(
            (
                "ix_prestamodesk_loan_collector_"
                "assignments_" + column
            ),
            table_name=(
                "prestamodesk_loan_collector_assignments"
            ),
        )

    op.drop_table(
        "prestamodesk_loan_collector_assignments"
    )

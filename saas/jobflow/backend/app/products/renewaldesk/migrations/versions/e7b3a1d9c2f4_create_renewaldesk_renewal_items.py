"""Create RenewalDesk renewal items

Revision ID: e7b3a1d9c2f4
Revises: c4d2e8a71f30
Create Date: 2026-08-20

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b3a1d9c2f4"
down_revision: Union[str, Sequence[str], None] = (
    "c4d2e8a71f30"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "renewaldesk_renewal_items",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "renewal_date",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f(
            "ix_renewaldesk_renewal_items_tenant_id"
        ),
        "renewaldesk_renewal_items",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_renewaldesk_renewal_items_tenant_id"
        ),
        table_name="renewaldesk_renewal_items",
    )

    op.drop_table(
        "renewaldesk_renewal_items"
    )

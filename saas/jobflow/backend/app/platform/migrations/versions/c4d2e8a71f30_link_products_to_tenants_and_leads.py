"""Link products to tenants and leads

Revision ID: c4d2e8a71f30
Revises: 9c8f41a2d7e0
Create Date: 2026-08-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d2e8a71f30"
down_revision: Union[str, Sequence[str], None] = "9c8f41a2d7e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "leads",
        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    jobflow_product_id = connection.execute(
        sa.text(
            """
            SELECT id
            FROM products
            WHERE slug = 'jobflow'
            """
        )
    ).scalar_one()

    # Existing production tenants belong to JobFlow.
    connection.execute(
        sa.text(
            """
            UPDATE tenants
            SET product_id = :product_id
            WHERE product_id IS NULL
            """
        ),
        {"product_id": jobflow_product_id},
    )

    # Commercialization was intentionally reset before this migration,
    # so no legacy leads need to be assigned implicitly.
    remaining_leads = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM leads
            WHERE product_id IS NULL
            """
        )
    ).scalar_one()

    if remaining_leads != 0:
        raise RuntimeError(
            "Cannot require leads.product_id while unassigned leads exist"
        )

    op.alter_column(
        "tenants",
        "product_id",
        nullable=False,
    )

    op.alter_column(
        "leads",
        "product_id",
        nullable=False,
    )

    op.create_index(
        op.f("ix_tenants_product_id"),
        "tenants",
        ["product_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_leads_product_id"),
        "leads",
        ["product_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_tenants_product_id_products",
        "tenants",
        "products",
        ["product_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_leads_product_id_products",
        "leads",
        "products",
        ["product_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_leads_product_id_products",
        "leads",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_tenants_product_id_products",
        "tenants",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_leads_product_id"),
        table_name="leads",
    )

    op.drop_index(
        op.f("ix_tenants_product_id"),
        table_name="tenants",
    )

    op.drop_column("leads", "product_id")
    op.drop_column("tenants", "product_id")

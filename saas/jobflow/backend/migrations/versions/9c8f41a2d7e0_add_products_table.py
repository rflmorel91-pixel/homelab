"""Add products table

Revision ID: 9c8f41a2d7e0
Revises: 58cf3d616a02
Create Date: 2026-08-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c8f41a2d7e0"
down_revision: Union[str, Sequence[str], None] = "58cf3d616a02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "workspace_key",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_products_slug"),
        "products",
        ["slug"],
        unique=True,
    )

    op.create_index(
        op.f("ix_products_status"),
        "products",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_products_workspace_key"),
        "products",
        ["workspace_key"],
        unique=True,
    )

    # Seed the existing application as the first platform product.
    op.execute(
        sa.text(
            """
            INSERT INTO products
                (name, slug, status, workspace_key, created_at)
            VALUES
                (
                    'JobFlow',
                    'jobflow',
                    'active',
                    'jobflow',
                    CURRENT_TIMESTAMP
                )
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_products_workspace_key"),
        table_name="products",
    )

    op.drop_index(
        op.f("ix_products_status"),
        table_name="products",
    )

    op.drop_index(
        op.f("ix_products_slug"),
        table_name="products",
    )

    op.drop_table("products")

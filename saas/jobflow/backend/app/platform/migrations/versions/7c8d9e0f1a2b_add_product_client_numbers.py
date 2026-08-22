"""Add product client numbers

Revision ID: 7c8d9e0f1a2b
Revises: 6b7c8d9e0f1a
Create Date: 2026-08-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c8d9e0f1a2b"
down_revision: Union[str, Sequence[str], None] = "6b7c8d9e0f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "client_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            WITH numbered_commercial_tenants AS (
                SELECT
                    tenants.id,
                    ROW_NUMBER() OVER (
                        PARTITION BY tenants.product_id
                        ORDER BY
                            leads.converted_at NULLS LAST,
                            tenants.id
                    )::integer AS client_number
                FROM tenants
                JOIN leads
                  ON leads.converted_tenant_id = tenants.id
                WHERE EXISTS (
                    SELECT 1
                    FROM user_invitations
                    WHERE
                        user_invitations.lead_id = leads.id
                        AND user_invitations.accepted_at
                            IS NOT NULL
                        AND user_invitations.revoked_at
                            IS NULL
                )
            )
            UPDATE tenants
            SET client_number =
                numbered_commercial_tenants.client_number
            FROM numbered_commercial_tenants
            WHERE
                tenants.id =
                    numbered_commercial_tenants.id
            """
        )
    )

    op.create_unique_constraint(
        "uq_tenants_product_client_number",
        "tenants",
        [
            "product_id",
            "client_number",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tenants_product_client_number",
        "tenants",
        type_="unique",
    )

    op.drop_column(
        "tenants",
        "client_number",
    )

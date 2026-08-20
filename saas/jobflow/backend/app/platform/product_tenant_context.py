from collections.abc import Callable

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Tenant
from app.tenant_context import get_current_tenant


def require_product_tenant(
    product_slug: str,
) -> Callable:
    def dependency(
        tenant: Tenant = Depends(get_current_tenant),
        db: Session = Depends(get_db),
    ) -> Tenant:
        product = db.scalar(
            select(Product).where(
                Product.slug == product_slug
            )
        )

        if (
            product is None
            or tenant.product_id != product.id
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Tenant does not belong "
                    "to this product"
                ),
            )

        return tenant

    return dependency

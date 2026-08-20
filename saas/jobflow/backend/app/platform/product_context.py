from collections.abc import Callable

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product


def require_active_product(
    slug: str,
) -> Callable:
    def dependency(
        db: Session = Depends(get_db),
    ) -> Product:
        product = db.scalar(
            select(Product).where(
                Product.slug == slug
            )
        )

        if product is None:
            raise HTTPException(
                status_code=503,
                detail="Product is unavailable",
            )

        if product.status != "active":
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Product is {product.status}"
                ),
            )

        return product

    return dependency

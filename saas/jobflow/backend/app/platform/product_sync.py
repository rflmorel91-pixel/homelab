from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.platform.products import ProductDefinition


class ProductSyncError(RuntimeError):
    pass


def synchronize_products(
    db: Session,
    definitions: tuple[ProductDefinition, ...],
) -> tuple[Product, ...]:
    synchronized: list[Product] = []

    for definition in definitions:
        existing = db.scalar(
            select(Product).where(
                Product.slug == definition.slug
            )
        )

        workspace_owner = db.scalar(
            select(Product).where(
                Product.workspace_key
                == definition.workspace_key
            )
        )

        if (
            workspace_owner is not None
            and (
                existing is None
                or workspace_owner.id != existing.id
            )
        ):
            raise ProductSyncError(
                "Installed product workspace_key conflicts "
                f"with database product: "
                f"{definition.workspace_key}"
            )

        if existing is None:
            existing = Product(
                name=definition.name,
                slug=definition.slug,
                status="active",
                workspace_key=definition.workspace_key,
            )
            db.add(existing)
            db.flush()

        else:
            # Developer-owned metadata may evolve with the
            # installed product package.
            existing.name = definition.name
            existing.workspace_key = (
                definition.workspace_key
            )

            # status is intentionally preserved because it is
            # platform/operator-owned runtime state.

        synchronized.append(existing)

    db.commit()

    for product in synchronized:
        db.refresh(product)

    return tuple(synchronized)

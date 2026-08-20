import argparse
from pathlib import Path
import re
import sys


SLUG_PATTERN = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
)


def python_package_name(slug: str) -> str:
    return slug.replace("-", "_")


def constant_name(slug: str) -> str:
    return (
        slug.replace("-", "_").upper()
        + "_PRODUCT"
    )


def create_product(
    *,
    root: Path,
    slug: str,
    name: str,
    description: str,
    resource: str | None = None,
) -> Path:
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(
            "slug must use lowercase letters, "
            "numbers, and hyphens"
        )

    package = python_package_name(slug)

    if resource is not None:
        if not re.fullmatch(
            r"[a-z][a-z0-9_]*",
            resource,
        ):
            raise ValueError(
                "resource must use lowercase letters, "
                "numbers, and underscores"
            )

        if not resource.isidentifier():
            raise ValueError(
                "resource must be a valid Python identifier"
            )

    if not package.isidentifier():
        raise ValueError(
            "slug does not produce a valid Python package"
        )

    product_dir = (
        root
        / "app"
        / "products"
        / package
    )

    if product_dir.exists():
        raise FileExistsError(
            f"product package already exists: {product_dir}"
        )

    tests_dir = root / "tests"

    product_dir.mkdir(
        parents=True,
    )
    tests_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    constant = constant_name(slug)

    api_prefix = (
        f"/api/v1/products/{slug}"
    )

    (product_dir / "__init__.py").write_text(
        f'''from app.products.{package}.definition import (
    {constant},
)

__all__ = [
    "{constant}",
]
'''
    )

    (product_dir / "api.py").write_text(
        f'''from fastapi import APIRouter


router = APIRouter(
    prefix="/status",
    tags=["{name}"],
)


@router.get("")
def {package}_status():
    return {{
        "product": "{slug}",
        "status": "available",
    }}
'''
    )

    if resource is None:
        definition_text = f'''from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.{package}.api import router


{constant} = register_product(
    ProductDefinition(
        slug="{slug}",
        name="{name}",
        version="0.1.0",
        workspace_key="{slug}",
        landing_route="/{slug}",
        workspace_route="/{slug}/app",
        api_prefix="{api_prefix}",
        routers=(
            router,
        ),
        description={description!r},
    )
)
'''
    else:
        definition_text = f'''from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.{package}.api import (
    router as status_router,
)
from app.products.{package}.{resource}s_api import (
    router as {resource}s_router,
)


{constant} = register_product(
    ProductDefinition(
        slug="{slug}",
        name="{name}",
        version="0.1.0",
        workspace_key="{slug}",
        landing_route="/{slug}",
        workspace_route="/{slug}/app",
        api_prefix="{api_prefix}",
        routers=(
            status_router,
        ),
        tenant_routers=(
            {resource}s_router,
        ),
        description={description!r},
    )
)
'''

    (product_dir / "definition.py").write_text(
        definition_text
    )

    if resource is not None:
        resource_class = "".join(
            part[:1].upper() + part[1:]
            for part in resource.split("_")
        )

        models_dir = product_dir / "models"
        migrations_dir = (
            product_dir
            / "migrations"
            / "versions"
        )

        models_dir.mkdir(
            parents=True,
        )
        migrations_dir.mkdir(
            parents=True,
        )

        (
            product_dir
            / "migrations"
            / "__init__.py"
        ).write_text("")

        model_class = resource_class

        (
            models_dir
            / f"{resource}.py"
        ).write_text(
            f'''from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class {model_class}(Base):
    __tablename__ = "{slug.replace("-", "_")}_{resource}s"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
'''
        )

        (
            models_dir
            / "__init__.py"
        ).write_text(
            f'''from app.products.{package}.models.{resource} import (
    {model_class},
)

__all__ = [
    "{model_class}",
]
'''
        )

        (
            product_dir
            / "schemas.py"
        ).write_text(
            f'''from datetime import datetime

from pydantic import BaseModel, ConfigDict


class {resource_class}Base(BaseModel):
    name: str


class {resource_class}Create({resource_class}Base):
    model_config = ConfigDict(
        extra="forbid",
    )


class {resource_class}Update({resource_class}Base):
    model_config = ConfigDict(
        extra="forbid",
    )


class {resource_class}Read({resource_class}Base):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
'''
        )

        (
            product_dir
            / f"{resource}s_api.py"
        ).write_text(
            f'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.{package}.models import {model_class}
from app.products.{package}.schemas import (
    {resource_class}Create,
    {resource_class}Read,
    {resource_class}Update,
)
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/{resource}s",
    tags=["{name} {resource_class}s"],
)


@router.post(
    "",
    response_model={resource_class}Read,
    status_code=201,
)
def create_{resource}(
    payload: {resource_class}Create,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = {model_class}(
        tenant_id=tenant.id,
        name=payload.name,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.get(
    "",
    response_model=list[{resource_class}Read],
)
def list_{resource}s(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select({model_class})
        .where(
            {model_class}.tenant_id
            == tenant.id
        )
        .order_by({model_class}.id)
    )

    return result.scalars().all()


@router.get(
    "/{{item_id}}",
    response_model={resource_class}Read,
)
def get_{resource}(
    item_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select({model_class}).where(
            {model_class}.id == item_id,
            {model_class}.tenant_id
            == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="{resource_class} not found",
        )

    return item


@router.put(
    "/{{item_id}}",
    response_model={resource_class}Read,
)
def update_{resource}(
    item_id: int,
    payload: {resource_class}Update,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select({model_class}).where(
            {model_class}.id == item_id,
            {model_class}.tenant_id
            == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="{resource_class} not found",
        )

    item.name = payload.name

    db.commit()
    db.refresh(item)

    return item


@router.delete(
    "/{{item_id}}",
    status_code=204,
)
def delete_{resource}(
    item_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select({model_class}).where(
            {model_class}.id == item_id,
            {model_class}.tenant_id
            == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="{resource_class} not found",
        )

    db.delete(item)
    db.commit()
'''
        )

    test_path = (
        tests_dir
        / f"test_{package}_product.py"
    )

    test_path.write_text(
        f'''from sqlalchemy import select

from app.models import Product
from app.platform import get_product


def test_{package}_is_discovered():
    definition = get_product("{slug}")

    assert definition is not None
    assert definition.name == "{name}"
    assert definition.workspace_key == "{slug}"


def test_{package}_router_is_composed(
    raw_client,
):
    response = raw_client.get(
        "{api_prefix}/status"
    )

    assert response.status_code == 200
    assert response.json() == {{
        "product": "{slug}",
        "status": "available",
    }}


def test_{package}_synchronizes_to_database(
    raw_client,
    db_session,
):
    response = raw_client.get(
        "{api_prefix}/status"
    )
    assert response.status_code == 200

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "{slug}"
        )
    )

    assert product is not None
    assert product.name == "{name}"
    assert product.status == "active"


def test_{package}_inherits_lifecycle(
    raw_client,
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "{slug}"
        )
    )

    assert product is not None

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "{api_prefix}/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )
'''
    )

    return product_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a product package for "
            "the SaaS platform."
        )
    )

    parser.add_argument(
        "slug",
        help="Product slug, e.g. client-portal",
    )

    parser.add_argument(
        "name",
        help="Human-readable product name",
    )

    parser.add_argument(
        "--description",
        default="SaaS product.",
    )

    parser.add_argument(
        "--with-resource",
        dest="resource",
        default=None,
        help=(
            "Generate tenant-scoped CRUD for a "
            "resource, e.g. asset"
        ),
    )

    args = parser.parse_args()

    backend_root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    try:
        product_dir = create_product(
            root=backend_root,
            slug=args.slug,
            name=args.name,
            description=args.description,
            resource=args.resource,
        )

    except (
        ValueError,
        FileExistsError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"Created product: {product_dir}")
    print(
        "No platform-core registration changes "
        "are required."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

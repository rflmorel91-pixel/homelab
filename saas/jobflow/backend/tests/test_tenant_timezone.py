import pytest

from sqlalchemy import select

from app.models import Product, Tenant


def test_tenant_defaults_to_utc_timezone(
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "jobflow"
        )
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        name="Default Timezone Tenant",
        slug="default-timezone-tenant",
    )

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.timezone_name == "UTC"


def test_tenant_supports_iana_timezone(
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "jobflow"
        )
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        name="Eastern Timezone Tenant",
        slug="eastern-timezone-tenant",
        timezone_name="America/New_York",
    )

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert (
        tenant.timezone_name
        == "America/New_York"
    )


def test_tenant_rejects_unknown_timezone(
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "jobflow"
        )
    )
    assert product is not None

    with pytest.raises(
        ValueError,
        match="Unknown IANA timezone",
    ):
        Tenant(
            product_id=product.id,
            name="Invalid Timezone Tenant",
            slug="invalid-timezone-tenant",
            timezone_name="Not/A_Timezone",
        )

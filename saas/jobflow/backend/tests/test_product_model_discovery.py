from app.database import Base
from app.platform import discover_product_models


def test_product_model_discovery_finds_renewaldesk():
    discovered = discover_product_models()

    assert "renewaldesk" in discovered


def test_renewaldesk_table_is_registered_in_metadata():
    discover_product_models()

    assert (
        "renewaldesk_renewal_items"
        in Base.metadata.tables
    )


def test_renewaldesk_table_has_tenant_boundary():
    discover_product_models()

    table = Base.metadata.tables[
        "renewaldesk_renewal_items"
    ]

    assert "tenant_id" in table.columns

    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key
        in table.columns["tenant_id"].foreign_keys
    }

    assert foreign_keys == {
        "tenants.id",
    }

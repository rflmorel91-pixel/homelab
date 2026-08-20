import pytest

from scripts.create_product import create_product


def test_create_product_generates_package(
    tmp_path,
):
    backend_root = tmp_path / "backend"

    product_dir = create_product(
        root=backend_root,
        slug="sample-product",
        name="Sample Product",
        description="Generated test product.",
    )

    assert product_dir.exists()
    assert (product_dir / "__init__.py").exists()
    assert (product_dir / "api.py").exists()
    assert (product_dir / "definition.py").exists()

    definition = (
        product_dir / "definition.py"
    ).read_text()

    assert 'slug="sample-product"' in definition
    assert 'name="Sample Product"' in definition
    assert (
        'api_prefix="/api/v1/products/sample-product"'
        in definition
    )

    generated_test = (
        backend_root
        / "tests"
        / "test_sample_product_product.py"
    )

    assert generated_test.exists()


def test_create_product_rejects_bad_slug(
    tmp_path,
):
    backend_root = tmp_path / "backend"

    with pytest.raises(ValueError):
        create_product(
            root=backend_root,
            slug="Bad Product",
            name="Bad Product",
            description="Invalid.",
        )


def test_create_product_refuses_overwrite(
    tmp_path,
):
    backend_root = tmp_path / "backend"

    (
        backend_root
        / "app"
        / "products"
        / "existing"
    ).mkdir(
        parents=True,
    )

    with pytest.raises(FileExistsError):
        create_product(
            root=backend_root,
            slug="existing",
            name="Existing",
            description="Existing product.",
        )


def test_create_product_with_resource_generates_data_layer(
    tmp_path,
):
    backend_root = tmp_path / "backend"

    product_dir = create_product(
        root=backend_root,
        slug="assettrack",
        name="AssetTrack",
        description="Track assets.",
        resource="asset",
    )

    assert (
        product_dir
        / "models"
        / "asset.py"
    ).exists()

    assert (
        product_dir
        / "models"
        / "__init__.py"
    ).exists()

    assert (
        product_dir
        / "schemas.py"
    ).exists()

    assert (
        product_dir
        / "assets_api.py"
    ).exists()

    assert (
        product_dir
        / "migrations"
        / "__init__.py"
    ).exists()

    assert (
        product_dir
        / "migrations"
        / "versions"
    ).is_dir()

    definition = (
        product_dir / "definition.py"
    ).read_text()

    assert "tenant_routers=(" in definition
    assert "assets_router" in definition

    model = (
        product_dir
        / "models"
        / "asset.py"
    ).read_text()

    assert (
        '__tablename__ = "assettrack_assets"'
        in model
    )

    assert 'ForeignKey("tenants.id")' in model

    schemas = (
        product_dir / "schemas.py"
    ).read_text()

    assert "extra=\"forbid\"" in schemas


@pytest.mark.parametrize(
    "resource",
    [
        "BadResource",
        "bad-resource",
        "bad resource",
        "1resource",
    ],
)
def test_create_product_rejects_bad_resource(
    tmp_path,
    resource,
):
    backend_root = tmp_path / "backend"

    with pytest.raises(ValueError):
        create_product(
            root=backend_root,
            slug="sample",
            name="Sample",
            description="Sample.",
            resource=resource,
        )


def test_generated_product_declares_platform_contract(
    tmp_path,
):
    backend_root = tmp_path / "backend"

    product_dir = create_product(
        root=backend_root,
        slug="contract-test",
        name="Contract Test",
        description="Contract version test.",
    )

    definition = (
        product_dir / "definition.py"
    ).read_text()

    assert (
        "platform_contract_version=1"
        in definition
    )


def test_generated_data_product_declares_platform_contract(
    tmp_path,
):
    backend_root = tmp_path / "backend"

    product_dir = create_product(
        root=backend_root,
        slug="data-contract-test",
        name="Data Contract Test",
        description="Data contract test.",
        resource="record",
    )

    definition = (
        product_dir / "definition.py"
    ).read_text()

    assert (
        "platform_contract_version=1"
        in definition
    )

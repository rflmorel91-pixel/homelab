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

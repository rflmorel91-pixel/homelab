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

    assert (
        product_dir
        / "migrations"
        / "versions"
        / "__init__.py"
    ).is_file()

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


def test_cli_defaults_to_current_working_directory(
    tmp_path,
    monkeypatch,
):
    from scripts.create_product import main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "saas-create-product",
            "workspace-proof",
            "Workspace Proof",
        ],
    )

    result = main()

    assert result == 0

    product_dir = (
        tmp_path
        / "app"
        / "products"
        / "workspace_proof"
    )

    assert product_dir.is_dir()
    assert (
        product_dir / "definition.py"
    ).is_file()


def test_create_standalone_product_generates_installable_project(
    tmp_path,
):
    from scripts.create_product import (
        create_standalone_product,
    )

    project_dir = create_standalone_product(
        root=tmp_path,
        slug="fieldops",
        name="FieldOps",
        description="Standalone external SaaS product.",
        resource="asset",
    )

    assert project_dir == (
        tmp_path / "fieldops-product"
    )

    product_dir = (
        project_dir
        / "saas_products"
        / "fieldops"
    )

    assert product_dir.is_dir()
    assert (product_dir / "__init__.py").is_file()
    assert (product_dir / "definition.py").is_file()
    assert (product_dir / "api.py").is_file()

    assert (
        product_dir
        / "models"
        / "asset.py"
    ).is_file()

    assert (
        product_dir
        / "migrations"
        / "versions"
    ).is_dir()

    assert (
        product_dir
        / "migrations"
        / "versions"
        / "__init__.py"
    ).is_file()

    assert (
        project_dir / "pyproject.toml"
    ).is_file()

    assert (
        project_dir / "README.md"
    ).is_file()

    assert (
        project_dir
        / "tests"
        / "test_fieldops_product.py"
    ).is_file()


def test_standalone_product_uses_plugin_namespace(
    tmp_path,
):
    from scripts.create_product import (
        create_standalone_product,
    )

    project_dir = create_standalone_product(
        root=tmp_path,
        slug="fieldops",
        name="FieldOps",
        description="Standalone.",
        resource="asset",
    )

    product_dir = (
        project_dir
        / "saas_products"
        / "fieldops"
    )

    generated_python = "\n".join(
        path.read_text()
        for path in product_dir.rglob("*.py")
    )

    assert "app.products.fieldops" not in generated_python

    assert (
        "saas_products.fieldops"
        in generated_python
    )


def test_standalone_pyproject_declares_platform_dependency(
    tmp_path,
):
    from scripts.create_product import (
        create_standalone_product,
    )

    project_dir = create_standalone_product(
        root=tmp_path,
        slug="fieldops",
        name="FieldOps",
        description="Standalone.",
        resource="asset",
    )

    pyproject = (
        project_dir / "pyproject.toml"
    ).read_text()

    assert (
        'name = "fieldops-product"'
        in pyproject
    )

    assert (
        '"jobflow-saas-platform==0.1.0"'
        in pyproject
    )

    assert (
        'include = ["saas_products.fieldops*"]'
        in pyproject
    )

    assert "namespaces = true" in pyproject


def test_standalone_product_refuses_overwrite(
    tmp_path,
):
    from scripts.create_product import (
        create_standalone_product,
    )

    project_dir = (
        tmp_path / "fieldops-product"
    )

    project_dir.mkdir()

    with pytest.raises(FileExistsError):
        create_standalone_product(
            root=tmp_path,
            slug="fieldops",
            name="FieldOps",
            description="Standalone.",
        )


def test_cli_generates_standalone_product(
    tmp_path,
    monkeypatch,
):
    from scripts.create_product import main

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "saas-create-product",
            "cli-plugin",
            "CLI Plugin",
            "--standalone",
            "--with-resource",
            "record",
        ],
    )

    result = main()

    assert result == 0

    project_dir = (
        tmp_path
        / "cli-plugin-product"
    )

    assert (
        project_dir
        / "saas_products"
        / "cli_plugin"
        / "definition.py"
    ).is_file()

    assert (
        project_dir
        / "saas_products"
        / "cli_plugin"
        / "models"
        / "record.py"
    ).is_file()

    assert (
        project_dir
        / "pyproject.toml"
    ).is_file()

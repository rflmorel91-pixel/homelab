from sqlalchemy import select

from app.models import Product
from app.platform import get_product


def test_workflow_automation_is_discovered():
    product = get_product("workflow-automation")

    assert product is not None
    assert product.name == (
        "Workflow Automation Package"
    )
    assert product.offering_type == "service"
    assert product.workspace_route is None
    assert product.tenant_routers == ()


def test_workflow_automation_router_is_composed(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/products/"
        "workflow-automation/status"
    )

    assert response.status_code == 200
    assert response.json() == {
        "product": "workflow-automation",
        "name": "Workflow Automation Package",
        "offering_type": "service",
        "status": "available",
    }


def test_workflow_automation_synchronizes_to_database(
    raw_client,
    db_session,
):
    response = raw_client.get(
        "/api/v1/products/"
        "workflow-automation/status"
    )

    assert response.status_code == 200

    product = db_session.scalar(
        select(Product).where(
            Product.slug
            == "workflow-automation"
        )
    )

    assert product is not None
    assert product.name == (
        "Workflow Automation Package"
    )
    assert product.workspace_key == (
        "workflow-automation"
    )
    assert product.status == "active"

def create_workflow_automation_lead(
    db_session,
    *,
    status="new",
):
    from app.models import Lead

    product = db_session.scalar(
        select(Product).where(
            Product.slug
            == "workflow-automation"
        )
    )

    assert product is not None

    lead = Lead(
        product_id=product.id,
        business_name="Automation Prospect",
        contact_name="Operations Manager",
        email="automation@example.com",
        service_type="Workflow assessment",
        message=(
            "We need to replace a spreadsheet "
            "and scheduled email process."
        ),
        status=status,
    )

    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    return lead


def make_platform_admin(
    db_session,
):
    from app.models import User

    user = db_session.scalar(
        select(User).where(
            User.email
            == "default-test-user@example.com"
        )
    )

    assert user is not None

    user.is_platform_admin = True
    db_session.commit()

    return user


def test_service_lead_uses_quote_workflow(
    client,
    db_session,
):
    make_platform_admin(db_session)

    lead = create_workflow_automation_lead(
        db_session
    )

    for next_status in (
        "contacted",
        "qualified",
        "quoted",
        "won",
    ):
        response = client.put(
            f"/api/v1/leads/{lead.id}",
            json={
                "status": next_status,
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["status"]
            == next_status
        )
        assert (
            response.json()["offering_type"]
            == "service"
        )

    db_session.refresh(lead)
    assert lead.status == "won"
    assert lead.converted_tenant_id is None


def test_service_lead_cannot_be_provisioned(
    client,
    db_session,
):
    operator = make_platform_admin(
        db_session
    )

    lead = create_workflow_automation_lead(
        db_session,
        status="qualified",
    )

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": operator.id,
            "tenant_slug": (
                "automation-prospect"
            ),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Service leads cannot be "
        "provisioned as clients"
    )

    db_session.refresh(lead)

    assert lead.status == "qualified"
    assert lead.converted_tenant_id is None


def test_saas_lead_cannot_use_service_status(
    client,
    db_session,
):
    from app.models import Lead

    make_platform_admin(db_session)

    jobflow = db_session.scalar(
        select(Product).where(
            Product.slug == "jobflow"
        )
    )

    assert jobflow is not None

    lead = Lead(
        product_id=jobflow.id,
        business_name="SaaS Prospect",
        contact_name="SaaS Contact",
        email="saas-status@example.com",
        service_type="Home services",
        status="qualified",
    )

    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "quoted",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid lead status transition: "
        "qualified -> quoted"
    )

def test_workflow_automation_public_page():
    from pathlib import Path

    workspace_root = (
        Path(__file__).resolve().parents[2]
    )

    page = (
        workspace_root
        / "app"
        / "workflow-automation.html"
    ).read_text()

    assert (
        "Workflow Automation Package"
        in page
    )
    assert "$500–$2,000 fixed" in page
    assert (
        "fixed-scope professional service"
        in page
    )
    assert (
        "/api/v1/public/products/"
        in page
    )
    assert (
        "workflow-automation/leads"
        in page
    )
    assert (
        "Request a workflow assessment"
        in page
    )
    assert "SaaS subscription" in page


def test_workflow_automation_nginx_route():
    from pathlib import Path

    workspace_root = (
        Path(__file__).resolve().parents[2]
    )

    nginx = (
        workspace_root
        / "nginx"
        / "default.conf"
    ).read_text()

    assert (
        "location = /workflow-automation"
        in nginx
    )
    assert (
        "try_files "
        "/workflow-automation.html =404;"
        in nginx
    )


def test_workflow_automation_public_lead(
    raw_client,
    db_session,
):
    from app.models import Lead

    response = raw_client.post(
        "/api/v1/public/products/"
        "workflow-automation/leads",
        json={
            "business_name": (
                "Automation Test Company"
            ),
            "contact_name": (
                "Automation Buyer"
            ),
            "email": (
                "automation-request@example.com"
            ),
            "phone": "555-0144",
            "service_type": (
                "Spreadsheet replacement"
            ),
            "message": (
                "Replace a manual intake and "
                "status-report spreadsheet."
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == (
        "received"
    )

    lead = db_session.get(
        Lead,
        response.json()["lead_id"],
    )

    product = db_session.scalar(
        select(Product).where(
            Product.slug
            == "workflow-automation"
        )
    )

    assert lead is not None
    assert product is not None
    assert lead.product_id == product.id
    assert lead.status == "new"
    assert lead.service_type == (
        "Spreadsheet replacement"
    )


def test_commercialization_separates_service_actions():
    from pathlib import Path

    workspace_root = (
        Path(__file__).resolve().parents[2]
    )

    page = (
        workspace_root
        / "app"
        / "commercialization.html"
    ).read_text()

    assert (
        'lead.offering_type === "service"'
        in page
    )
    assert (
        'lead.offering_type !== "service"'
        in page
    )
    assert '["quoted", "Mark Quoted"]' in page
    assert '["won", "Mark Won"]' in page
    assert 'quoted: "Quoted"' in page
    assert 'won: "Won"' in page


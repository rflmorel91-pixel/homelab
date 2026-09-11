from hashlib import sha256
from pathlib import Path

from sqlalchemy import select

from app.models import Lead, Product


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_assettrack_landing_page_has_pilot_offer_and_lead_form():
    page = (WORKSPACE_ROOT / "app" / "assettrack.html").read_text()
    script = (
        WORKSPACE_ROOT
        / "app"
        / "assets"
        / "assettrack-15188ad30017.js"
    ).read_text()

    assert "AssetTrack Developer API" in page
    assert "$99 one-time" in page
    assert "$49 per month" in page
    assert 'id="pilotForm"' in page
    assert "/api/v1/public/products/assettrack/leads" in script
    assert "before requesting payment" in script


def test_assettrack_landing_page_assets_are_content_hashed():
    for name in (
        "assettrack-bba1c615168c.css",
        "assettrack-15188ad30017.js",
    ):
        content = (WORKSPACE_ROOT / "app" / "assets" / name).read_bytes()
        assert sha256(content).hexdigest()[:12] in name


def test_assettrack_pilot_application_is_owned_by_assettrack(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/products/assettrack/leads",
        json={
            "business_name": "Small IT Partner",
            "contact_name": "Pilot Developer",
            "email": "assettrack-pilot@example.com",
            "phone": None,
            "service_type": "AssetTrack pilot — Small IT firm",
            "message": (
                "Assets to track: Customer workstations\n\n"
                "System or workflow: Internal service portal\n\n"
                "Problem to solve: Duplicate spreadsheet entry\n\n"
                "Preferred start date: 2026-09-15"
            ),
        },
    )

    assert response.status_code == 201

    product = db_session.scalar(
        select(Product).where(Product.slug == "assettrack")
    )
    lead = db_session.get(Lead, response.json()["lead_id"])

    assert product is not None
    assert lead is not None
    assert lead.product_id == product.id
    assert lead.status == "new"
    assert lead.service_type == "AssetTrack pilot — Small IT firm"

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import Product, Tenant, TenantMembership
from app.products.prestamodesk.models import Borrower, Installment, Loan, LoanApplication, Prospect

BASE = "/api/v1/products/prestamodesk"


def setup(db, client, *, status="qualified", slug="routing-tenant"):
    product = db.scalar(select(Product).where(Product.slug == "prestamodesk"))
    tenant = Tenant(product_id=product.id, name="Routing test", slug=slug, client_number=81)
    db.add(tenant)
    db.flush()
    prospect = Prospect(tenant_id=tenant.id, full_name="Synthetic Applicant", phone="809-555-0100",
        email="synthetic@example.test", requested_amount=Decimal("30000.00"), status=status,
        consented_at=datetime.now(timezone.utc), consent_notice_version="2026-09-29")
    db.add(prospect)
    db.commit()
    return tenant, prospect, client.owner_headers(tenant)


def terms(kind="personal"):
    payload = dict(loan_type=kind, principal_amount="30000.00", flat_interest_rate_percent="10",
        installment_count=12, payment_frequency="monthly", start_date="2026-10-05", first_payment_date="2026-11-05")
    if kind == "vehicle":
        payload.update(vehicle_cash_price="1000000.00", vehicle_down_payment="200000.00",
            vehicle_make="Toyota", vehicle_model="Corolla", vehicle_year=2022, principal_amount="800000.00")
    return payload


@pytest.mark.parametrize("kind", ["personal", "vehicle"])
def test_prospect_route_review_approval_conversion(db_session, authenticated_client, kind):
    db, client = db_session, authenticated_client
    tenant, prospect, headers = setup(db, client)
    payload = terms(kind)
    quote = client.post(f"{BASE}/applications/quote", headers=headers, json=payload)
    assert quote.status_code == 200
    assert len(quote.json()["installments"]) == 12
    expected_total = Decimal(payload["principal_amount"]) * Decimal("1.10")
    assert sum(Decimal(item["total_due"]) for item in quote.json()["installments"]) == expected_total
    assert db.scalar(select(func.count()).select_from(LoanApplication)) == 0
    response = client.post(f"{BASE}/prospects/{prospect.id}/application", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["source_prospect_id"] == prospect.id
    assert body["loan_type"] == kind and body["status"] == "new"
    assert body["full_name"] == prospect.full_name
    assert body["consent_notice_version"] == prospect.consent_notice_version
    assert (body["vehicle_make"] is None) == (kind == "personal")
    assert db.scalar(select(func.count()).select_from(Borrower)) == 0
    url = f"{BASE}/applications/{body['id']}"
    assert client.post(url + "/convert", headers=headers).status_code == 409
    assert client.put(url, headers=headers, json={"status":"approved"}).status_code == 409
    reviewing = client.put(
        url, headers=headers, json={"status": "reviewing"}
    )
    assert reviewing.status_code == 200, reviewing.text

    packet = {
        "inspection": {
            "status": "passed",
            "inspector_name": "Inspector Sintético",
            "inspected_at": "2026-10-01T10:00:00Z",
            "findings": "Inspección documentada",
        },
        "documents": [
            {
                "document_type": "identity",
                "status": "verified",
                "storage_ref": "11111111-1111-4111-8111-111111111111",
                "checked_at": "2026-10-01T10:00:00Z",
            },
            {
                "document_type": "income",
                "status": "verified",
                "storage_ref": "22222222-2222-4222-8222-222222222222",
                "checked_at": "2026-10-01T10:00:00Z",
            },
        ],
        "references": [{
            "full_name": "Referencia Sintética",
            "relationship": "Familiar",
            "phone": "809-555-0199",
            "status": "contacted",
            "outcome_notes": "Identidad confirmada; referencia positiva.",
        }],
        "assessment": {
            "income_source": "Empleo",
            "monthly_net_income": "95000.00",
            "monthly_obligations": "12000.00",
            "affordability_summary":
                "Capacidad revisada contra obligaciones declaradas.",
            "recommendation": "approve",
        },
        "contract": {
            "status": "signed",
            "template_version": "pilot-v1",
            "signed_at": "2026-10-02T12:00:00Z",
            "signed_copy_ref": "44444444-4444-4444-8444-444444444444",
        },
    }
    if kind == "vehicle":
        packet["documents"].append({
            "document_type": "vehicle_registration",
            "status": "verified",
            "storage_ref": "33333333-3333-4333-8333-333333333333",
            "checked_at": "2026-10-01T10:00:00Z",
        })

    synthetic_pdf = b"%PDF-1.4\\nSynthetic private test document\\n"
    for document in packet["documents"]:
        uploaded = client.put(
            f"{url}/documents/{document['document_type']}",
            headers={**headers, "Content-Type": "application/pdf"},
            content=synthetic_pdf,
        )
        assert uploaded.status_code == 201, uploaded.text
        document["storage_ref"] = uploaded.json()["storage_ref"]

    contract_upload = client.put(
        f"{url}/documents/contract",
        headers={**headers, "Content-Type": "application/pdf"},
        content=synthetic_pdf,
    )
    assert contract_upload.status_code == 201, contract_upload.text
    packet["contract"]["signed_copy_ref"] = contract_upload.json()["storage_ref"]

    saved_packet = client.put(
        f"{url}/review-packet", headers=headers, json=packet
    )
    assert saved_packet.status_code == 200, saved_packet.text

    approved = client.put(url, headers=headers, json={
        "status": "approved",
        "decision_reason": "Evaluación favorable documentada.",
    })
    assert approved.status_code == 200, approved.text
    result = client.post(url + "/convert", headers=headers)
    assert result.status_code == 201, result.text
    db.expire_all()
    loan = db.get(Loan, result.json()["loan_id"])
    assert loan.loan_type == kind and loan.total_due == expected_total
    assert loan.tenant_id == tenant.id
    assert db.scalar(select(func.count()).select_from(Installment).where(Installment.loan_id == loan.id)) == 12
    assert db.get(Prospect, prospect.id).converted_borrower_id == loan.borrower_id
    assert db.get(Prospect, prospect.id).status == "converted"
    assert client.post(url + "/convert", headers=headers).status_code == 409
    assert client.post(f"{BASE}/prospects/{prospect.id}/application", headers=headers, json=payload).status_code == 409
    assert db.scalar(select(func.count()).select_from(Borrower)) == 1


def test_application_blocks_duplicate_and_legacy_conversion(db_session, authenticated_client):
    db, client = db_session, authenticated_client
    _, prospect, headers = setup(db, client)
    url = f"{BASE}/prospects/{prospect.id}"
    assert client.post(url + "/application", headers=headers, json=terms()).status_code == 201
    assert client.post(url + "/application", headers=headers, json=terms("vehicle")).status_code == 409
    assert client.post(url + "/convert", headers=headers).status_code == 409
    assert client.put(url, headers=headers, json={"status":"rejected"}).status_code == 409
    assert db.scalar(select(func.count()).select_from(LoanApplication)) == 1
    assert db.scalar(select(func.count()).select_from(Borrower)) == 0


@pytest.mark.parametrize("status", ["new", "contacted", "rejected", "converted"])
def test_route_requires_qualified_prospect(db_session, authenticated_client, status):
    _, prospect, headers = setup(db_session, authenticated_client, status=status)
    result = authenticated_client.post(f"{BASE}/prospects/{prospect.id}/application", headers=headers, json=terms())
    assert result.status_code == 409


def test_internal_routes_tenant_and_role_isolation(db_session, authenticated_client, raw_client):
    db, client = db_session, authenticated_client
    tenant, prospect, headers = setup(db, client)
    other = Tenant(product_id=tenant.product_id, name="Other", slug="other-routing-tenant")
    db.add(other)
    db.commit()
    other_headers = client.owner_headers(other)
    url = f"{BASE}/prospects/{prospect.id}/application"
    assert client.post(url, headers=other_headers, json=terms()).status_code == 404
    assert raw_client.post(url, json=terms()).status_code == 401
    assert raw_client.post(f"{BASE}/applications/quote", json=terms()).status_code == 401
    member = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant.id))
    member.role = "cashier"
    db.commit()
    assert client.post(url, headers=headers, json=terms()).status_code == 403
    assert client.post(f"{BASE}/applications/quote", headers=headers, json=terms()).status_code == 403


@pytest.mark.parametrize("patch", [
    {"vehicle_make":"Toyota"}, {"loan_type":"other"}, {"principal_amount":"0"},
    {"first_payment_date":"2026-10-01"}, {"tenant_id":999}, {"full_name":"Forged Applicant"},
])
def test_invalid_personal_terms_rejected(db_session, authenticated_client, patch):
    _, prospect, headers = setup(db_session, authenticated_client)
    payload = {**terms(), **patch}
    for url in [f"{BASE}/applications/quote", f"{BASE}/prospects/{prospect.id}/application"]:
        assert authenticated_client.post(url, headers=headers, json=payload).status_code == 422


@pytest.mark.parametrize("patch", [
    {"vehicle_make":"   "}, {"vehicle_down_payment":"1000000.00"}, {"principal_amount":"100.00"},
    {"vehicle_year":None}, {"vehicle_make":None},
])
def test_invalid_vehicle_terms_rejected(db_session, authenticated_client, patch):
    _, prospect, headers = setup(db_session, authenticated_client)
    response = authenticated_client.post(f"{BASE}/prospects/{prospect.id}/application", headers=headers, json={**terms("vehicle"), **patch})
    assert response.status_code == 422


def test_rejected_application_does_not_create_loan(db_session, authenticated_client):
    db, client = db_session, authenticated_client
    _, prospect, headers = setup(db, client)
    body = client.post(f"{BASE}/prospects/{prospect.id}/application", headers=headers, json=terms()).json()
    url = f"{BASE}/applications/{body['id']}"
    assert client.put(url, headers=headers, json={"status":"reviewing"}).status_code == 200
    assert client.put(
        url, headers=headers,
        json={
            "status": "rejected",
            "decision_reason": "Rechazo documentado tras revisión.",
        },
    ).status_code == 200
    assert client.post(url + "/convert", headers=headers).status_code == 409
    assert db.scalar(select(func.count()).select_from(Loan)) == 0


def test_schema_prevents_duplicate_prospect_link(db_session, authenticated_client):
    from sqlalchemy.exc import IntegrityError
    db, client = db_session, authenticated_client
    _, prospect, headers = setup(db, client)
    original = client.post(f"{BASE}/prospects/{prospect.id}/application", headers=headers, json=terms()).json()
    application = db.get(LoanApplication, original["id"])
    values = {column.name: getattr(application, column.name) for column in LoanApplication.__table__.columns if column.name != "id"}
    db.add(LoanApplication(**values))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.scalar(select(func.count()).select_from(LoanApplication)) == 1


def test_migration_preserves_vehicle_history_and_guards_downgrade():
    import importlib
    from sqlalchemy import create_engine, Column, Integer, MetaData, Table, String, inspect
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    migration = importlib.import_module("app.products.prestamodesk.migrations.versions.f9b1d3e5a7c0_prospect_application_routes")
    metadata = MetaData()
    Table("prestamodesk_prospects", metadata, Column("id", Integer, primary_key=True))
    applications = Table("prestamodesk_applications", metadata, Column("id", Integer, primary_key=True),
        Column("loan_type", String(30), nullable=False),
        *(Column(name, kind, nullable=False) for name, kind in migration.VEHICLE_COLUMNS.items()))
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(applications.insert().values(id=1, loan_type="vehicle", vehicle_cash_price=1000000,
            vehicle_down_payment=200000, vehicle_make="Toyota", vehicle_model="Corolla", vehicle_year=2022))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        refreshed = Table("prestamodesk_applications", MetaData(), autoload_with=connection)
        assert connection.execute(select(refreshed.c.vehicle_make)).scalar_one() == "Toyota"
        assert connection.execute(select(refreshed.c.source_prospect_id)).scalar_one() is None
        connection.execute(refreshed.insert().values(id=2, loan_type="personal"))
        with Operations.context(MigrationContext.configure(connection)):
            with pytest.raises(RuntimeError, match="history cannot be discarded"):
                migration.downgrade()
        connection.execute(refreshed.delete().where(refreshed.c.id == 2))
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        columns = {item["name"]: item for item in inspect(connection).get_columns("prestamodesk_applications")}
        assert "source_prospect_id" not in columns
        assert all(not columns[name]["nullable"] for name in migration.VEHICLE_COLUMNS)

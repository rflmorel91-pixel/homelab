from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.models import Product, Tenant
from app.products.prestamodesk.models import (
    ApplicationReview,
    ApplicationReviewDocument,
    Borrower,
    Installment,
    Loan,
    LoanApplication,
)


APPLICATIONS_URL = (
    "/api/v1/products/prestamodesk/applications"
)


def upload_document(client, headers, application, document_type):
    response = client.put(
        f"{APPLICATIONS_URL}/{application.id}/documents/{document_type}",
        headers={**headers, "Content-Type": "application/pdf"},
        content=b"%PDF-1.4\nSynthetic private test document\n",
    )
    assert response.status_code == 201, response.text
    return response.json()["storage_ref"]


def complete_packet(*, signed_contract=True):
    packet = {
        "inspection": {
            "status": "passed",
            "inspector_name": "Inspector Sintético",
            "inspected_at": "2026-10-01T10:00:00Z",
            "findings": "Inspección documentada",
        },
        "documents": [
            {
                "document_type": kind,
                "status": "verified",
                "storage_ref": ref,
                "checked_at": "2026-10-01T10:00:00Z",
            }
            for kind, ref in (
                ("identity", "11111111-1111-4111-8111-111111111111"),
                ("income", "22222222-2222-4222-8222-222222222222"),
                ("vehicle_registration", "33333333-3333-4333-8333-333333333333"),
            )
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
            "affordability_summary": "Capacidad revisada contra obligaciones declaradas.",
            "recommendation": "approve",
        },
        "contract": {
            "status": "signed" if signed_contract else "prepared",
            "template_version": "pilot-v1" if signed_contract else None,
            "signed_at": "2026-10-02T12:00:00Z" if signed_contract else None,
            "signed_copy_ref": "44444444-4444-4444-8444-444444444444" if signed_contract else None,
        },
    }
    return packet


def get_product(db_session):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None
    return product


def create_tenant(
    db_session,
    product,
    name,
    slug,
):
    tenant = Tenant(
        product_id=product.id,
        name=name,
        slug=slug,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def create_application(
    db_session,
    tenant,
    *,
    status="new",
    name="Solicitante Sintético",
):
    application = LoanApplication(
        tenant_id=tenant.id,
        full_name=name,
        document_type="cedula",
        document_number="001-0000000-1",
        phone="809-555-0102",
        email="solicitante@example.test",
        address="Dirección sintética",
        municipality="Santo Domingo Este",
        province="Santo Domingo",
        loan_type="vehicle",
        vehicle_cash_price=Decimal("1000000.00"),
        vehicle_down_payment=Decimal("200000.00"),
        vehicle_make="Toyota",
        vehicle_model="Corolla",
        vehicle_year=2022,
        vehicle_color="Blanco",
        vehicle_vin="SYNTHETIC-APPLICATION-001",
        vehicle_license_plate="TEST002",
        vehicle_seller="Dealer Sintético",
        vehicle_notes="Vehículo sintético",
        principal_amount=Decimal("800000.00"),
        flat_interest_rate_percent=Decimal("10.0000"),
        total_interest=Decimal("80000.00"),
        total_due=Decimal("880000.00"),
        installment_count=12,
        payment_frequency="monthly",
        start_date=date(2026, 9, 30),
        first_payment_date=date(2026, 10, 29),
        currency="DOP",
        status=status,
        notes="Solicitud sintética",
        consented_at=datetime.now(timezone.utc),
        consent_notice_version="2026-09-30",
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    if status == "approved":
        application.decision_reason = "Expediente revisado y aprobado para piloto."
        packet = complete_packet()
        application.review_packet = ApplicationReview(
            tenant_id=tenant.id,
            packet=packet,
        )
        for item in packet["documents"] + [{
            "document_type": "contract",
            "storage_ref": packet["contract"]["signed_copy_ref"],
        }]:
            db_session.add(ApplicationReviewDocument(
                storage_ref=item["storage_ref"],
                tenant_id=tenant.id,
                application_id=application.id,
                document_type=item["document_type"],
                content_type="application/pdf",
                byte_size=32,
                sha256="0" * 64,
                file_key=f"{tenant.id}/{application.id}/{item['storage_ref']}.pdf",
            ))
        db_session.commit()
    return application


def test_tenant_can_list_and_view_own_applications(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application List Tenant",
        "application-list-tenant",
    )
    application = create_application(
        db_session,
        tenant,
    )
    headers = client.owner_headers(tenant)

    list_response = client.get(
        APPLICATIONS_URL,
        headers=headers,
    )
    assert list_response.status_code == 200
    assert [
        item["id"]
        for item in list_response.json()
    ] == [application.id]

    get_response = client.get(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["full_name"] == (
        "Solicitante Sintético"
    )


def test_applications_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant_a = create_tenant(
        db_session,
        product,
        "Application Tenant A",
        "application-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Application Tenant B",
        "application-tenant-b",
    )
    application = create_application(
        db_session,
        tenant_a,
    )

    response = client.get(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=client.owner_headers(tenant_b),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Application not found"
    )


def test_application_follows_review_and_approval_flow(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application Workflow Tenant",
        "application-workflow-tenant",
    )
    application = create_application(
        db_session,
        tenant,
    )
    headers = client.owner_headers(tenant)
    url = f"{APPLICATIONS_URL}/{application.id}"

    reviewing = client.put(
        url,
        headers=headers,
        json={"status": "reviewing"},
    )
    assert reviewing.status_code == 200
    assert reviewing.json()["status"] == "reviewing"
    assert reviewing.json()["reviewed_at"] is not None

    packet_data = complete_packet(signed_contract=False)
    for item in packet_data["documents"]:
        item["storage_ref"] = upload_document(
            client, headers, application, item["document_type"]
        )
    packet = client.put(
        f"{url}/review-packet",
        headers=headers,
        json=packet_data,
    )
    assert packet.status_code == 200
    assert packet.json()["assessment"]["recommendation"] == "approve"

    approved = client.put(
        url,
        headers=headers,
        json={"status": "approved", "decision_reason": "Capacidad documentada para el piloto."},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["approved_at"] is not None


def test_application_cannot_skip_review(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application Transition Tenant",
        "application-transition-tenant",
    )
    application = create_application(
        db_session,
        tenant,
    )

    response = client.put(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=client.owner_headers(tenant),
        json={"status": "approved"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Application cannot move from new to approved"
    )

    db_session.refresh(application)
    assert application.status == "new"


def test_approval_requires_complete_review_packet_and_reason(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(db_session, product, "Review Gate Tenant", "review-gate-tenant")
    application = create_application(db_session, tenant, status="reviewing")
    headers = client.owner_headers(tenant)

    missing_packet = client.put(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=headers,
        json={"status": "approved", "decision_reason": "Revisión terminada."},
    )
    assert missing_packet.status_code == 409
    assert "identity document must be verified" in missing_packet.json()["detail"]["gaps"]

    incomplete = complete_packet()
    incomplete["documents"] = [item for item in incomplete["documents"] if item["document_type"] != "income"]
    for item in incomplete["documents"]:
        item["storage_ref"] = upload_document(
            client, headers, application, item["document_type"]
        )
    saved = client.put(
        f"{APPLICATIONS_URL}/{application.id}/review-packet",
        headers=headers,
        json=incomplete,
    )
    assert saved.status_code == 200
    response = client.put(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=headers,
        json={"status": "approved", "decision_reason": "Revisión terminada."},
    )
    assert response.status_code == 409
    assert "income document must be verified" in response.json()["detail"]["gaps"]


def test_conversion_waits_for_signed_contract_and_review_is_audited(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(db_session, product, "Contract Gate Tenant", "contract-gate-tenant")
    application = create_application(db_session, tenant, status="reviewing")
    headers = client.owner_headers(tenant)
    url = f"{APPLICATIONS_URL}/{application.id}"

    initial_packet = complete_packet(signed_contract=False)
    for item in initial_packet["documents"]:
        item["storage_ref"] = upload_document(
            client, headers, application, item["document_type"]
        )
    saved = client.put(f"{url}/review-packet", headers=headers, json=initial_packet)
    assert saved.status_code == 200
    approved = client.put(url, headers=headers, json={
        "status": "approved", "decision_reason": "Evaluación favorable documentada.",
    })
    assert approved.status_code == 200

    blocked = client.post(f"{url}/convert", headers=headers)
    assert blocked.status_code == 409
    assert "signed contract" in blocked.json()["detail"]

    signed = complete_packet()
    signed["contract"]["signed_copy_ref"] = upload_document(
        client, headers, application, "contract"
    )
    signed["inspection"] = complete_packet(signed_contract=False)["inspection"]
    signed["documents"] = initial_packet["documents"]
    signed["references"] = complete_packet(signed_contract=False)["references"]
    signed["assessment"] = complete_packet(signed_contract=False)["assessment"]
    updated = client.put(f"{url}/review-packet", headers=headers, json=signed)
    assert updated.status_code == 200

    converted = client.post(f"{url}/convert", headers=headers)
    assert converted.status_code == 201
    events = client.get(f"{url}/review-events", headers=headers)
    assert events.status_code == 200
    assert [event["event_type"] for event in events.json()] == [
        "document_uploaded", "document_uploaded", "document_uploaded",
        "packet_updated", "approved", "document_uploaded",
        "packet_updated", "converted",
    ]


def test_unapproved_application_cannot_be_converted(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Unapproved Application Tenant",
        "unapproved-application-tenant",
    )
    application = create_application(
        db_session,
        tenant,
        status="reviewing",
    )

    response = client.post(
        (
            f"{APPLICATIONS_URL}/{application.id}"
            "/convert"
        ),
        headers=client.owner_headers(tenant),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Application must be approved before conversion"
    )
    assert db_session.scalar(
        select(Borrower.id).where(
            Borrower.tenant_id == tenant.id
        )
    ) is None
    assert db_session.scalar(
        select(Loan.id).where(
            Loan.tenant_id == tenant.id
        )
    ) is None


def test_approved_application_converts_atomically(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application Conversion Tenant",
        "application-conversion-tenant",
    )
    application = create_application(
        db_session,
        tenant,
        status="approved",
        name="Pedro Sánchez",
    )

    response = client.post(
        (
            f"{APPLICATIONS_URL}/{application.id}"
            "/convert"
        ),
        headers=client.owner_headers(tenant),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["application_id"] == application.id
    assert body["status"] == "converted"

    borrower = db_session.get(
        Borrower,
        body["borrower_id"],
    )
    loan = db_session.get(
        Loan,
        body["loan_id"],
    )

    assert borrower is not None
    assert borrower.tenant_id == tenant.id
    assert borrower.full_name == "Pedro Sánchez"
    assert borrower.document_number == "001-0000000-1"

    assert loan is not None
    assert loan.tenant_id == tenant.id
    assert loan.borrower_id == borrower.id
    assert loan.loan_type == "vehicle"
    assert loan.vehicle_make == "Toyota"
    assert loan.vehicle_model == "Corolla"
    assert loan.principal_amount == Decimal("800000.00")
    assert loan.total_interest == Decimal("80000.00")
    assert loan.total_due == Decimal("880000.00")
    assert loan.status == "active"

    installment_count = db_session.scalar(
        select(func.count(Installment.id)).where(
            Installment.loan_id == loan.id
        )
    )
    assert installment_count == 12

    installment_total = db_session.scalar(
        select(func.sum(Installment.total_due)).where(
            Installment.loan_id == loan.id
        )
    )
    assert installment_total == Decimal("880000.00")

    db_session.refresh(application)
    assert application.status == "converted"
    assert application.converted_borrower_id == borrower.id
    assert application.converted_loan_id == loan.id
    assert application.converted_at is not None


def test_application_conversion_cannot_repeat(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Repeat Application Conversion Tenant",
        "repeat-application-conversion-tenant",
    )
    application = create_application(
        db_session,
        tenant,
        status="approved",
    )
    headers = client.owner_headers(tenant)
    url = (
        f"{APPLICATIONS_URL}/{application.id}/convert"
    )

    first = client.post(
        url,
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        url,
        headers=headers,
    )
    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Application has already been converted"
    )

    assert db_session.scalar(
        select(func.count(Borrower.id)).where(
            Borrower.tenant_id == tenant.id
        )
    ) == 1
    assert db_session.scalar(
        select(func.count(Loan.id)).where(
            Loan.tenant_id == tenant.id
        )
    ) == 1


def test_application_conversion_cannot_cross_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant_a = create_tenant(
        db_session,
        product,
        "Conversion Application Tenant A",
        "conversion-application-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Conversion Application Tenant B",
        "conversion-application-b",
    )
    application = create_application(
        db_session,
        tenant_a,
        status="approved",
    )

    response = client.post(
        (
            f"{APPLICATIONS_URL}/{application.id}"
            "/convert"
        ),
        headers=client.owner_headers(tenant_b),
    )

    assert response.status_code == 404
    assert db_session.scalar(
        select(Borrower.id).where(
            Borrower.tenant_id == tenant_b.id
        )
    ) is None
    assert db_session.scalar(
        select(Loan.id).where(
            Loan.tenant_id == tenant_b.id
        )
    ) is None


def test_private_application_document_upload_and_tenant_scoped_download(
    authenticated_client, db_session, monkeypatch, tmp_path,
):
    from app.products.prestamodesk.private_documents import MAX_PRIVATE_DOCUMENT_BYTES

    monkeypatch.setenv("PRESTAMODESK_PRIVATE_STORAGE_PATH", str(tmp_path))
    product = get_product(db_session)
    tenant_a = create_tenant(db_session, product, "Private Docs A", "private-docs-a")
    tenant_b = create_tenant(db_session, product, "Private Docs B", "private-docs-b")
    application = create_application(db_session, tenant_a, status="reviewing")
    headers = authenticated_client.owner_headers(tenant_a)
    upload_url = f"{APPLICATIONS_URL}/{application.id}/documents/identity"
    data = b"%PDF-1.7\nsynthetic private identity\n"

    uploaded = authenticated_client.put(
        upload_url,
        headers={**headers, "Content-Type": "application/pdf"},
        content=data,
    )
    assert uploaded.status_code == 201, uploaded.text
    metadata = uploaded.json()
    assert metadata["document_type"] == "identity"
    assert metadata["byte_size"] == len(data)
    assert metadata["sha256"]
    assert "/" not in metadata["storage_ref"]

    download_url = f"{upload_url}/{metadata['storage_ref']}"
    downloaded = authenticated_client.get(download_url, headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.content == data
    assert downloaded.headers["cache-control"] == "private, no-store"
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in downloaded.headers["content-disposition"]

    cross_tenant = authenticated_client.get(
        download_url, headers=authenticated_client.owner_headers(tenant_b)
    )
    assert cross_tenant.status_code == 404

    invalid = authenticated_client.put(
        upload_url,
        headers={**headers, "Content-Type": "application/pdf"},
        content=b"not a pdf",
    )
    assert invalid.status_code == 415

    oversized = authenticated_client.put(
        upload_url,
        headers={**headers, "Content-Type": "application/pdf"},
        content=b"%PDF-1.7\n" + b"x" * MAX_PRIVATE_DOCUMENT_BYTES,
    )
    assert oversized.status_code == 413


def test_private_document_role_permissions(authenticated_client, db_session):
    from sqlalchemy import select
    from app.models import TenantMembership

    client = authenticated_client
    tenant = create_tenant(
        db_session, get_product(db_session),
        "Document Roles", "document-roles",
    )
    application = create_application(db_session, tenant, status="reviewing")
    headers = client.owner_headers(tenant)
    ref = upload_document(client, headers, application, "identity")
    upload_url = f"{APPLICATIONS_URL}/{application.id}/documents/identity"
    download_url = f"{upload_url}/{ref}"
    membership = db_session.scalar(select(TenantMembership).where(
        TenantMembership.tenant_id == tenant.id,
        TenantMembership.user_id == client.auth_user.id,
    ))

    for role in (
        "owner", "administrator", "member",
        "cashier", "collector", "supervisor",
    ):
        membership.role = role
        db_session.commit()
        allowed = role in {"owner", "administrator"}

        downloaded = client.get(download_url, headers=headers)
        assert downloaded.status_code == (200 if allowed else 403), role
        if allowed:
            assert downloaded.content.startswith(b"%PDF-")
            assert downloaded.headers["cache-control"] == "private, no-store"
        else:
            assert b"%PDF-" not in downloaded.content

        uploaded = client.put(
            upload_url,
            headers={**headers, "Content-Type": "application/pdf"},
            content=b"%PDF-1.4\nSynthetic role test\n",
        )
        assert uploaded.status_code == (201 if allowed else 403), role

    membership.role = "owner"
    membership.is_active = False
    db_session.commit()
    assert client.get(download_url, headers=headers).status_code == 403
    assert client.put(
        upload_url,
        headers={**headers, "Content-Type": "application/pdf"},
        content=b"%PDF-1.4\nInactive membership\n",
    ).status_code == 403


def test_private_documents_require_auth_and_matching_url(
    authenticated_client, db_session, raw_client,
):
    from uuid import uuid4

    client = authenticated_client
    tenant = create_tenant(
        db_session, get_product(db_session),
        "Document URLs", "document-urls",
    )
    application = create_application(db_session, tenant, status="reviewing")
    other_application = create_application(
        db_session, tenant, status="reviewing",
    )
    headers = client.owner_headers(tenant)
    ref = upload_document(client, headers, application, "identity")
    upload_url = f"{APPLICATIONS_URL}/{application.id}/documents/identity"
    download_url = f"{upload_url}/{ref}"

    response = raw_client.get(download_url)
    assert response.status_code == 401
    assert b"%PDF-" not in response.content
    assert raw_client.put(
        upload_url, headers={"Content-Type": "application/pdf"},
        content=b"%PDF-1.4\nUnauthenticated upload\n",
    ).status_code == 401

    for url in (
        f"{APPLICATIONS_URL}/{other_application.id}/documents/identity/{ref}",
        f"{APPLICATIONS_URL}/{application.id}/documents/income/{ref}",
        f"{upload_url}/{uuid4()}",
    ):
        response = client.get(url, headers=headers)
        assert response.status_code == 404
        assert b"%PDF-" not in response.content

    response = client.get(f"{upload_url}/invalid-reference", headers=headers)
    assert response.status_code == 422


def test_private_storage_rejects_paths_outside_root(tmp_path, monkeypatch):
    import pytest
    from app.products.prestamodesk.private_documents import private_document_path

    root = tmp_path / "private"
    root.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-1.4\nSynthetic outside file\n")
    monkeypatch.setenv("PRESTAMODESK_PRIVATE_STORAGE_PATH", str(root))

    inside = root / "inside.pdf"
    inside.write_bytes(b"%PDF-1.4\nSynthetic inside file\n")
    assert private_document_path("inside.pdf") == inside

    (root / "escape.pdf").symlink_to(outside)
    for key in ("../outside.pdf", str(outside), "escape.pdf", "missing.pdf"):
        with pytest.raises(FileNotFoundError):
            private_document_path(key)

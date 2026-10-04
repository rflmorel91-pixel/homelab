import hashlib
import io
import json
from zipfile import ZipFile

import pytest
from sqlalchemy import select

from app.models import AdminAuditLog, TenantMembership, UserInvitation
from app.products.prestamodesk import customer_export_api as exports
from tests.test_prestamodesk_payments import create_borrower, create_tenant, get_product, create_two_installment_loan

URL = "/api/v1/products/prestamodesk/administration/export.zip"


def role_headers(client, db, tenant, role):
    headers = client.owner_headers(tenant)
    membership = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant.id))
    membership.role = role
    db.commit()
    return headers


def setup_tenant(db):
    return create_tenant(db, get_product(db), "Export Client", "export-client")


def test_export_is_scoped_portable_and_audited(authenticated_client, db_session):
    client = authenticated_client
    tenant = setup_tenant(db_session)
    borrower = create_borrower(db_session, tenant, '=HYPERLINK("https://example.test")')
    other = create_tenant(db_session, get_product(db_session), "Other", "other-export")
    create_borrower(db_session, other, "PRIVATE OTHER TENANT")
    loan = create_two_installment_loan(client, tenant, borrower)
    payment = client.post("/api/v1/products/prestamodesk/payments", headers=client.owner_headers(tenant), json={
        "installment_id": loan["installments"][0]["id"], "amount": "100.00", "paid_at": "2026-10-04T12:00:00"})
    assert payment.status_code == 201, payment.text
    void = client.post(f'/api/v1/products/prestamodesk/payments/{payment.json()["id"]}/void',
                       headers=client.owner_headers(tenant), json={"reason": "Export test correction"})
    assert void.status_code == 200
    response = client.post(URL, headers=client.owner_headers(tenant))
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    with ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        records = json.loads(archive.read("records.json"))
        assert records["borrowers"][0]["full_name"] == borrower.full_name
        assert b"PRIVATE OTHER TENANT" not in archive.read("records.json")
        assert "'=" in archive.read("borrowers.csv").decode("utf-8-sig")
        assert records["payments"][0]["amount"] == "100.00"
        assert records["payments"][0]["void_reason"] == "Export test correction"
        assert records["payments"][0]["correction_snapshot"] is not None
        assert records["team"][0]["email"]
        assert "password_hash" not in records["team"][0]
        assert "is_platform_admin" not in records["team"][0]
        assert len(records["installments"]) == 2
        assert records["audit_history"][0]["action"] == "payments.voided"
        for name, info in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == info["sha256"]
        for name, count in manifest["row_counts"].items():
            assert count == len(records[name])
    audit = db_session.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "customer_data.exported"))
    assert audit.tenant_id == tenant.id


@pytest.mark.parametrize("role", ["member", "collector", "cashier", "supervisor"])
def test_export_denied_for_operational_roles(authenticated_client, db_session, role):
    tenant = setup_tenant(db_session)
    assert authenticated_client.post(URL, headers=role_headers(authenticated_client, db_session, tenant, role)).status_code == 403


def test_administrator_and_empty_export(authenticated_client, db_session):
    tenant = setup_tenant(db_session)
    response = authenticated_client.post(URL, headers=role_headers(authenticated_client, db_session, tenant, "administrator"))
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.read("borrowers.csv").startswith(b"\xef\xbb\xbf")
        assert json.loads(archive.read("records.json"))["borrowers"] == []


@pytest.mark.parametrize("value", ["=1+1", " +SUM(A1)", "-cmd", "@sum", "\ttext", "\ntext", "\rtext"])
def test_formula_text_is_escaped(value):
    assert exports.csv_cell(value) == "'" + value


def test_limits_fail_without_download_or_audit(authenticated_client, db_session, monkeypatch):
    tenant = setup_tenant(db_session)
    monkeypatch.setattr(exports, "MAX_ROWS", 0)
    response = authenticated_client.post(URL, headers=authenticated_client.owner_headers(tenant))
    assert response.status_code == 413
    assert db_session.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "customer_data.exported")) is None


def test_bytes_limit(authenticated_client, db_session, monkeypatch):
    tenant = setup_tenant(db_session)
    monkeypatch.setattr(exports, "MAX_BYTES", 1)
    assert authenticated_client.post(URL, headers=authenticated_client.owner_headers(tenant)).status_code == 413


def test_anonymous_export_denied(raw_client):
    assert raw_client.post(URL).status_code == 401


def test_suspended_membership_denied(authenticated_client, db_session):
    tenant = setup_tenant(db_session)
    headers = authenticated_client.owner_headers(tenant)
    membership = db_session.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant.id))
    membership.is_active = False
    db_session.commit()
    assert authenticated_client.post(URL, headers=headers).status_code == 403


def test_invitations_exclude_tokens_and_other_tenants(authenticated_client, db_session):
    from datetime import datetime, timedelta
    tenant = setup_tenant(db_session)
    headers = authenticated_client.owner_headers(tenant)
    actor = db_session.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant.id))
    invitation = UserInvitation(tenant_id=tenant.id, email="invite@example.test", display_name="Invite",
        role="cashier", token_hash="SECRET_HASH_DO_NOT_EXPORT", created_by_user_id=actor.user_id,
        expires_at=datetime.now() + timedelta(days=1))
    db_session.add(invitation)
    db_session.commit()
    response = authenticated_client.post(URL, headers=headers)
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as archive:
        for name in archive.namelist():
            assert b"SECRET_HASH_DO_NOT_EXPORT" not in archive.read(name)
        record = json.loads(archive.read("records.json"))["invitations"][0]
        assert record["email"] == "invite@example.test"
        assert "token_hash" not in record


def test_snapshot_rechecks_role(db_session, authenticated_client):
    tenant = setup_tenant(db_session)
    role_headers(authenticated_client, db_session, tenant, "cashier")
    actor = db_session.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant.id))
    from fastapi import HTTPException
    with db_session.get_bind().connect() as connection:
        with pytest.raises(HTTPException) as error:
            exports.export_snapshot(connection, tenant.id, actor.user_id)
        assert error.value.status_code == 403

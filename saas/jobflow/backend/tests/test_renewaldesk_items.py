from sqlalchemy import select

from app.models import Product, Tenant
from app.products.renewaldesk.models import RenewalItem


ITEMS_URL = "/api/v1/products/renewaldesk/items"


def get_product(
    db_session,
    slug,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == slug
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


def test_renewaldesk_tenant_can_crud_items(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk CRUD Tenant",
        "renewaldesk-crud-tenant",
    )

    headers = client.auth_headers(tenant)

    create_response = client.post(
        ITEMS_URL,
        headers=headers,
        json={
            "name": "Contractor License",
            "renewal_date": "2027-03-15",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    assert created["name"] == (
        "Contractor License"
    )
    assert created["renewal_date"] == (
        "2027-03-15"
    )

    item_id = created["id"]

    stored = db_session.get(
        RenewalItem,
        item_id,
    )

    assert stored is not None
    assert stored.tenant_id == tenant.id

    list_response = client.get(
        ITEMS_URL,
        headers=headers,
    )

    assert list_response.status_code == 200
    assert [
        item["id"]
        for item in list_response.json()
    ] == [item_id]

    get_response = client.get(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == item_id

    update_response = client.put(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
        json={
            "name": "Updated Contractor License",
            "renewal_date": "2027-04-20",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == (
        "Updated Contractor License"
    )

    delete_response = client.delete(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    missing = client.get(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
    )

    assert missing.status_code == 404


def test_renewaldesk_items_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant_a = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Tenant A",
        "renewaldesk-tenant-a",
    )

    tenant_b = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Tenant B",
        "renewaldesk-tenant-b",
    )

    create_response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(
            tenant_a
        ),
        json={
            "name": "Tenant A License",
            "renewal_date": "2027-01-01",
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = client.get(
        f"{ITEMS_URL}/{item_id}",
        headers=client.auth_headers(
            tenant_b
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Renewal item not found"
    )

    list_response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(
            tenant_b
        ),
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_jobflow_tenant_cannot_use_renewaldesk_items(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    jobflow = get_product(
        db_session,
        "jobflow",
    )

    tenant = create_tenant(
        db_session,
        jobflow,
        "JobFlow Wrong Product Tenant",
        "jobflow-wrong-product-tenant",
    )

    response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant does not belong to this product"
    )


def test_suspended_renewaldesk_tenant_is_blocked(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "Suspended RenewalDesk Tenant",
        "suspended-renewaldesk-tenant",
    )

    tenant.status = "suspended"
    db_session.commit()

    response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant is suspended"
    )


def test_suspended_renewaldesk_product_is_blocked(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "Product Suspension Tenant",
        "product-suspension-tenant",
    )

    renewaldesk.status = "suspended"
    db_session.commit()

    response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )


def test_client_cannot_supply_tenant_id(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant_a = create_tenant(
        db_session,
        renewaldesk,
        "Trusted Tenant",
        "trusted-renewaldesk-tenant",
    )

    tenant_b = create_tenant(
        db_session,
        renewaldesk,
        "Target Tenant",
        "target-renewaldesk-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(
            tenant_a
        ),
        json={
            "name": "Attempted Tenant Override",
            "renewal_date": "2027-06-01",
            "tenant_id": tenant_b.id,
        },
    )

    assert response.status_code == 422

    stored = db_session.scalars(
        select(RenewalItem)
    ).all()

    assert stored == []


def test_renewaldesk_item_supports_commercial_fields(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Commercial Tenant",
        "renewaldesk-commercial-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "General Liability Insurance",
            "category": "insurance",
            "renewal_date": "2027-02-01",
            "status": "active",
            "owner_name": "Office Manager",
            "reminder_days": 60,
            "notes": "Renew with current carrier.",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["name"] == (
        "General Liability Insurance"
    )
    assert payload["category"] == "insurance"
    assert payload["status"] == "active"
    assert payload["owner_name"] == "Office Manager"
    assert payload["reminder_days"] == 60
    assert payload["notes"] == (
        "Renew with current carrier."
    )
    assert payload["created_at"] is not None
    assert payload["updated_at"] is not None


def test_renewaldesk_item_defaults_are_safe(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Defaults Tenant",
        "renewaldesk-defaults-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Contractor License",
            "renewal_date": "2027-03-15",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["category"] == "other"
    assert payload["status"] == "active"
    assert payload["owner_name"] is None
    assert payload["reminder_days"] == 30
    assert payload["notes"] is None


def test_renewaldesk_rejects_invalid_status(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Invalid Status Tenant",
        "renewaldesk-invalid-status-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Business License",
            "renewal_date": "2027-01-01",
            "status": "overdue",
        },
    )

    assert response.status_code == 422


def test_renewaldesk_rejects_invalid_reminder_days(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Reminder Tenant",
        "renewaldesk-reminder-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Insurance",
            "renewal_date": "2027-04-01",
            "reminder_days": -1,
        },
    )

    assert response.status_code == 422


def test_renewaldesk_item_reports_upcoming_renewal(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from datetime import date

    from app.products.renewaldesk import schemas

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 1)

    monkeypatch.setattr(
        schemas,
        "date",
        FixedDate,
    )

    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Upcoming Tenant",
        "renewaldesk-upcoming-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Business License",
            "renewal_date": "2027-04-01",
            "reminder_days": 30,
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["renewal_state"] == "upcoming"
    assert payload["days_until_renewal"] == 90


def test_renewaldesk_item_reports_due_soon(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from datetime import date

    from app.products.renewaldesk import schemas

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 1)

    monkeypatch.setattr(
        schemas,
        "date",
        FixedDate,
    )

    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Due Soon Tenant",
        "renewaldesk-due-soon-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Insurance",
            "renewal_date": "2027-01-20",
            "reminder_days": 30,
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["renewal_state"] == "due_soon"
    assert payload["days_until_renewal"] == 19


def test_renewaldesk_item_reports_expired(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from datetime import date

    from app.products.renewaldesk import schemas

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 15)

    monkeypatch.setattr(
        schemas,
        "date",
        FixedDate,
    )

    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Expired Tenant",
        "renewaldesk-expired-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Contractor License",
            "renewal_date": "2027-01-10",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["renewal_state"] == "expired"
    assert payload["days_until_renewal"] == -5


def test_inactive_renewaldesk_item_reports_inactive(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from datetime import date

    from app.products.renewaldesk import schemas

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 15)

    monkeypatch.setattr(
        schemas,
        "date",
        FixedDate,
    )

    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Inactive Tenant",
        "renewaldesk-inactive-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Old Insurance Policy",
            "renewal_date": "2027-01-10",
            "status": "inactive",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["renewal_state"] == "inactive"
    assert payload["days_until_renewal"] == -5


DASHBOARD_URL = "/api/v1/products/renewaldesk/dashboard"


def test_renewaldesk_dashboard_summarizes_renewals(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from datetime import date

    from app.products.renewaldesk import schemas

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 15)

    monkeypatch.setattr(
        schemas,
        "date",
        FixedDate,
    )

    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Dashboard Tenant",
        "renewaldesk-dashboard-tenant",
    )

    headers = client.auth_headers(tenant)

    items = [
        {
            "name": "Expired License",
            "renewal_date": "2027-01-10",
            "reminder_days": 30,
        },
        {
            "name": "Insurance Due Soon",
            "renewal_date": "2027-01-25",
            "reminder_days": 30,
        },
        {
            "name": "Upcoming Permit",
            "renewal_date": "2027-04-15",
            "reminder_days": 30,
        },
        {
            "name": "Inactive Registration",
            "renewal_date": "2027-01-01",
            "status": "inactive",
        },
    ]

    for item in items:
        response = client.post(
            ITEMS_URL,
            headers=headers,
            json=item,
        )

        assert response.status_code == 201

    response = client.get(
        DASHBOARD_URL,
        headers=headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 4
    assert payload["expired"] == 1
    assert payload["due_soon"] == 1
    assert payload["upcoming"] == 1
    assert payload["inactive"] == 1

    assert [
        item["name"]
        for item in payload["items"]
    ] == [
        "Expired License",
        "Insurance Due Soon",
        "Upcoming Permit",
        "Inactive Registration",
    ]


def test_renewaldesk_dashboard_is_tenant_scoped(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant_a = create_tenant(
        db_session,
        renewaldesk,
        "Dashboard Tenant A",
        "dashboard-tenant-a",
    )

    tenant_b = create_tenant(
        db_session,
        renewaldesk,
        "Dashboard Tenant B",
        "dashboard-tenant-b",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(
            tenant_a
        ),
        json={
            "name": "Tenant A License",
            "renewal_date": "2027-06-01",
        },
    )

    assert response.status_code == 201

    response = client.get(
        DASHBOARD_URL,
        headers=client.auth_headers(
            tenant_b
        ),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 0
    assert payload["expired"] == 0
    assert payload["due_soon"] == 0
    assert payload["upcoming"] == 0
    assert payload["inactive"] == 0
    assert payload["items"] == []


def test_jobflow_tenant_cannot_use_renewaldesk_dashboard(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    jobflow = get_product(
        db_session,
        "jobflow",
    )

    tenant = create_tenant(
        db_session,
        jobflow,
        "Wrong Product Dashboard Tenant",
        "wrong-product-dashboard-tenant",
    )

    response = client.get(
        DASHBOARD_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant does not belong to this product"
    )

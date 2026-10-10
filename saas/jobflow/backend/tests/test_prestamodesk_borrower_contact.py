import pytest
from app.models import TenantMembership
from tests.test_prestamodesk_administration import add_member, headers
from tests.test_prestamodesk_collections import create_tenant

BASE = '/api/v1/products/prestamodesk/borrowers'


def create_record(client, h):
    response = client.post(BASE, headers=h, json={
        'full_name': 'SYNTHETIC Contact', 'document_type': 'other',
        'document_number': 'SYN-CONTACT-001', 'status': 'inactive',
        'phone': '809-555-0101', 'email': 'old@example.test',
        'address': 'Synthetic address', 'municipality': 'Santiago',
        'province': 'Santiago', 'notes': 'Synthetic note',
    })
    assert response.status_code == 201
    return response.json()


def payload(record):
    return {key: record[key] for key in ('phone', 'email', 'address', 'municipality', 'province', 'notes')} | {
        'expected_updated_at': record['updated_at']}


@pytest.mark.parametrize('role', ['owner', 'administrator'])
def test_contact_preserves_identity_and_rejects_stale_edit(raw_client, db_session, role):
    tenant = create_tenant(db_session, client_number=980, slug='contact-preserve')
    user, _ = add_member(db_session, tenant, role, 'contact')
    h = headers(user, tenant)
    record = create_record(raw_client, h)
    values = payload(record) | {'phone': ' 809-555-0102 ', 'email': ' new@example.test ', 'notes': ' '}
    url = f"{BASE}/{record['id']}/contact"
    saved = raw_client.patch(url, headers=h, json=values)
    assert saved.status_code == 200
    data = saved.json()
    assert data['phone'] == '809-555-0102'
    assert data['email'] == 'new@example.test'
    assert data['notes'] is None
    for key in ('id', 'full_name', 'document_type', 'document_number', 'status', 'created_at'):
        assert data[key] == record[key]
    assert data['updated_at'] != record['updated_at']
    assert raw_client.patch(url, headers=h, json=values).status_code == 409
    current = raw_client.get(f"{BASE}/{record['id']}", headers=h).json()
    assert current == data
    cleared = raw_client.patch(url, headers=h, json=payload(data) | {'phone': None, 'email': None})
    assert cleared.status_code == 200
    assert cleared.json()['phone'] is None


def test_full_update_invalidates_contact_snapshot(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=981, slug='contact-put')
    user, _ = add_member(db_session, tenant, 'owner', 'contact-put')
    h = headers(user, tenant)
    record = create_record(raw_client, h)
    values = {k: v for k, v in record.items() if k not in ('id', 'created_at', 'updated_at')}
    values['full_name'] = 'SYNTHETIC Renamed'
    updated = raw_client.put(f"{BASE}/{record['id']}", headers=h, json=values)
    assert updated.status_code == 200
    assert updated.json()['updated_at'] != record['updated_at']
    assert raw_client.patch(f"{BASE}/{record['id']}/contact", headers=h, json=payload(record)).status_code == 409


@pytest.mark.parametrize('role', ['member', 'cashier', 'collector', 'supervisor'])
def test_contact_denies_other_roles(raw_client, db_session, role):
    tenant = create_tenant(db_session, client_number=982, slug='contact-denied')
    owner, _ = add_member(db_session, tenant, 'owner', 'contact-owner')
    record = create_record(raw_client, headers(owner, tenant))
    user, _ = add_member(db_session, tenant, role, 'contact-worker')
    assert raw_client.patch(f"{BASE}/{record['id']}/contact", headers=headers(user, tenant), json=payload(record)).status_code == 403


def test_contact_tenant_and_suspension_enforcement(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=983, slug='contact-isolation')
    other = create_tenant(db_session, client_number=984, slug='contact-foreign')
    owner, membership = add_member(db_session, tenant, 'owner', 'contact-isolation')
    foreign, _ = add_member(db_session, other, 'owner', 'contact-foreign')
    h = headers(owner, tenant)
    record = create_record(raw_client, h)
    url = f"{BASE}/{record['id']}/contact"
    assert raw_client.patch(url, headers=headers(foreign, other), json=payload(record)).status_code == 404
    membership.is_active = False
    db_session.commit()
    assert raw_client.patch(url, headers=h, json=payload(record)).status_code == 403


@pytest.mark.parametrize('extra', [{'email': 'bad'}, {'phone': 'x' * 41}, {'province': 'x' * 121}, {'address': 'x' * 2001}, {'notes': 'x' * 5001}, {'status': 'active'}, {'full_name': 'Changed'}, {'expected_updated_at': 'invalid'}])
def test_contact_validation_is_atomic(raw_client, db_session, extra):
    tenant = create_tenant(db_session, client_number=985, slug='contact-validation')
    owner, _ = add_member(db_session, tenant, 'owner', 'contact-validation')
    h = headers(owner, tenant)
    record = create_record(raw_client, h)
    assert raw_client.patch(f"{BASE}/{record['id']}/contact", headers=h, json=payload(record) | extra).status_code == 422
    assert raw_client.get(f"{BASE}/{record['id']}", headers=h).json() == record

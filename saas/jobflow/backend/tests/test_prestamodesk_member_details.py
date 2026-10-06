from datetime import datetime
import pytest
from sqlalchemy import select, func
from app.models import AdminAuditLog, TenantMembership, User
from app.products.prestamodesk.models import MemberProfile
from app.products.prestamodesk import administration_api as api
from tests.test_prestamodesk_administration import add_member, headers, ADMIN
from tests.test_prestamodesk_collections import create_tenant, create_loan, BASE_URL


def setup(db):
    tenant = create_tenant(db, client_number=980, slug="member-detail")
    owner, _ = add_member(db, tenant, "owner", "detail-owner")
    target, membership = add_member(db, tenant, "collector", "detail-collector")
    return tenant, owner, target, membership


def test_profile_is_business_scoped_not_global(raw_client, db_session):
    db=db_session
    tenant,owner,target,membership=setup(db)
    other=create_tenant(db, client_number=981, slug="member-other")
    other_membership=TenantMembership(tenant_id=other.id,user_id=target.id,role="collector")
    db.add(other_membership);db.commit()
    other_owner,_=add_member(db,other,"owner","detail-other-owner")
    url=f"{ADMIN}/memberships/{membership.id}"
    original_email,original_name=target.email,target.display_name
    h=headers(owner,tenant)
    response=raw_client.get(url,headers=h)
    assert response.status_code==200 and response.headers["cache-control"]=="no-store"
    assert response.json()["profile"]["phone"] is None
    payload={"contact_name":"  Business Contact  ","phone":"809-555-0100","correspondence_email":" CONTACT@EXAMPLE.TEST ","preferred_contact":"phone","notes":" Reference only "}
    result=raw_client.put(url+"/profile",headers=h,json=payload)
    assert result.status_code==200,result.text
    assert result.json()["profile"]["correspondence_email"]=="contact@example.test"
    detail=raw_client.get(url,headers=h).json()
    assert detail["profile"]["contact_name"]=="Business Contact"
    assert any(item["action"]=="client_team.profile_changed" for item in detail["history"])
    db.refresh(target)
    assert target.email==original_email and target.display_name==original_name
    other_detail=raw_client.get(f"{ADMIN}/memberships/{other_membership.id}",headers=headers(other_owner,other)).json()
    assert other_detail["profile"]["phone"] is None
    normalized=result.json()["profile"]
    assert raw_client.put(url+"/profile",headers=h,json=normalized).status_code==200
    assert db.scalar(select(func.count()).select_from(AdminAuditLog).where(AdminAuditLog.action=="client_team.profile_changed"))==1
    assert db.scalar(select(func.count()).select_from(MemberProfile))==1
    for forbidden in ["password_hash","token_hash","password","reset_token"]:
        assert forbidden not in detail


@pytest.mark.parametrize("role",["collector","cashier","member","supervisor"])
def test_details_require_administration_role(raw_client,db_session,role):
    tenant,_,_,membership=setup(db_session)
    user,_=add_member(db_session,tenant,role,"detail-denied")
    url=f"{ADMIN}/memberships/{membership.id}"
    for method,suffix,payload in [("get","",None),("put","/profile",{}),("post","/password-reset",None)]:
        kwargs={"headers":headers(user,tenant)}
        if payload is not None:kwargs["json"]=payload
        assert getattr(raw_client,method)(url+suffix,**kwargs).status_code==403


def test_cross_tenant_details_and_mutations_denied(raw_client,db_session):
    tenant,_,_,membership=setup(db_session)
    other=create_tenant(db_session,client_number=982,slug="other-detail-scope")
    owner,_=add_member(db_session,other,"owner","scope-owner")
    h=headers(owner,other);url=f"{ADMIN}/memberships/{membership.id}"
    assert raw_client.get(url,headers=h).status_code==404
    assert raw_client.put(url+"/profile",headers=h,json={}).status_code==404
    assert raw_client.post(url+"/password-reset",headers=h).status_code==404
    assert raw_client.get(url).status_code==401


def test_admin_profile_edit_rules_match_privileged_roles(raw_client,db_session):
    tenant,owner,_,membership=setup(db_session)
    admin,admin_membership=add_member(db_session,tenant,"administrator","details-admin")
    owner_membership=db_session.scalar(select(TenantMembership).where(TenantMembership.tenant_id==tenant.id,TenantMembership.user_id==owner.id))
    h=headers(admin,tenant)
    assert raw_client.get(f"{ADMIN}/memberships/{owner_membership.id}",headers=h).json()["editable"] is False
    assert raw_client.put(f"{ADMIN}/memberships/{owner_membership.id}/profile",headers=h,json={"phone":"123"}).status_code==403
    assert raw_client.put(f"{ADMIN}/memberships/{admin_membership.id}/profile",headers=h,json={"phone":"123"}).status_code==403
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/profile",headers=h,json={"phone":"123"}).status_code==200


@pytest.mark.parametrize("payload",[{"correspondence_email":"not-email"},{"phone":"x"*41},{"role":"owner"},{"email":"changed@example.test"},{"user_id":1},{"notes":"x"*2001},{"preferred_contact":"sms"}])
def test_profile_validation(raw_client,db_session,payload):
    tenant,owner,_,membership=setup(db_session)
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/profile",headers=headers(owner,tenant),json=payload).status_code==422


def test_assignments_and_history_are_specific_to_member(raw_client,db_session):
    db=db_session;tenant,owner,collector,membership=setup(db)
    another,other_membership=add_member(db,tenant,"collector","other-collector-detail")
    _,loan,_=create_loan(db,tenant=tenant,suffix=983)
    h=headers(owner,tenant)
    assert raw_client.post(f"{BASE_URL}/collections/loans/{loan.id}/assignment",headers=h,json={"collector_user_id":collector.id}).status_code==200
    detail=raw_client.get(f"{ADMIN}/memberships/{membership.id}",headers=h).json()
    assert [row["loan_id"] for row in detail["assignments"]]==[loan.id]
    assert any(row["action"]=="collections.assignment_created" for row in detail["history"])
    other=raw_client.get(f"{ADMIN}/memberships/{other_membership.id}",headers=h).json()
    assert other["assignments"]==[] and other["history"]==[]
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/status",headers=h,json={"is_active":False}).status_code==409
    assert raw_client.post(f"{BASE_URL}/collections/loans/{loan.id}/assignment/release",headers=h,json={"reason":"Reassign"}).status_code==200
    detail=raw_client.get(f"{ADMIN}/memberships/{membership.id}",headers=h).json()
    assert detail["assignments"]==[]
    assert {row["action"] for row in detail["history"]}>={"collections.assignment_created","collections.assignment_released"}


def test_recovery_uses_login_email_and_never_exposes_token(raw_client,db_session,monkeypatch):
    tenant,owner,target,membership=setup(db_session)
    called=[]
    def fake(payload,db):
        called.append(payload.model_dump());return {"status":"accepted","message":"Generic recovery response"}
    monkeypatch.setattr(api,"request_password_reset",fake)
    h=headers(owner,tenant);url=f"{ADMIN}/memberships/{membership.id}"
    assert raw_client.put(url+"/profile",headers=h,json={"correspondence_email":"other@example.test"}).status_code==200
    result=raw_client.post(url+"/password-reset",headers=h)
    assert result.status_code==200 and result.json()["status"]=="accepted"
    assert called==[{"email":target.email,"product_slug":"prestamodesk"}]
    history=raw_client.get(url,headers=h).json()["history"]
    assert any(row["action"]=="client_team.password_reset_requested" for row in history)
    assert raw_client.put(url+"/status",headers=h,json={"is_active":False}).status_code==200
    assert raw_client.post(url+"/password-reset",headers=h).status_code==409
    assert len(called)==1


def test_profile_export_and_history_included(raw_client,db_session):
    import io,json
    from zipfile import ZipFile
    from app.products.prestamodesk.customer_export_api import export_snapshot,create_archive
    tenant,owner,target,membership=setup(db_session)
    h=headers(owner,tenant)
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/profile",headers=h,json={"phone":"809-555-0100"}).status_code==200
    # The shared export helper reads the same metadata on both supported databases.
    with db_session.get_bind().connect() as connection:
        datasets=export_snapshot(connection,tenant.id,owner.id)
    archive,_=create_archive(datasets,tenant.id,owner.id)
    with ZipFile(io.BytesIO(archive)) as zipped:
        records=json.loads(zipped.read("records.json"))
    assert records["member_profiles"][0]["phone"]=="809-555-0100"
    assert any(event["action"]=="client_team.profile_changed" for event in records["audit_history"])


def test_member_profile_migration_and_downgrade_guard():
    import importlib
    from sqlalchemy import create_engine, MetaData, Table, Column, Integer, inspect
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    migration=importlib.import_module("app.products.prestamodesk.migrations.versions.a0c2e4f6b8d1_member_profiles")
    engine=create_engine("sqlite:///:memory:");metadata=MetaData()
    tenants=Table("tenants",metadata,Column("id",Integer,primary_key=True))
    memberships=Table("tenant_memberships",metadata,Column("id",Integer,primary_key=True))
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(tenants.insert().values(id=1));connection.execute(memberships.insert().values(id=1))
        with Operations.context(MigrationContext.configure(connection)):migration.upgrade()
        profiles=Table("prestamodesk_member_profiles",MetaData(),autoload_with=connection)
        connection.execute(profiles.insert().values(tenant_id=1,membership_id=1,phone="809-555-0100",preferred_contact="phone",updated_at=datetime.now()))
        with Operations.context(MigrationContext.configure(connection)):
            with pytest.raises(RuntimeError,match="contact records cannot be discarded"):migration.downgrade()
        assert connection.execute(select(profiles.c.phone)).scalar_one()=="809-555-0100"
        connection.execute(profiles.delete())
        with Operations.context(MigrationContext.configure(connection)):migration.downgrade()
        assert "prestamodesk_member_profiles" not in inspect(connection).get_table_names()


def test_administrator_cannot_request_privileged_recovery(raw_client,db_session,monkeypatch):
    tenant,owner,_,_=setup(db_session)
    admin,admin_membership=add_member(db_session,tenant,"administrator","recovery-admin")
    owner_membership=db_session.scalar(select(TenantMembership).where(TenantMembership.tenant_id==tenant.id,TenantMembership.user_id==owner.id))
    def forbidden_call(*args,**kwargs):raise AssertionError("Privileged recovery reached mail flow")
    monkeypatch.setattr(api,"request_password_reset",forbidden_call)
    h=headers(admin,tenant)
    for membership in [owner_membership,admin_membership]:
        assert raw_client.post(f"{ADMIN}/memberships/{membership.id}/password-reset",headers=h).status_code==403

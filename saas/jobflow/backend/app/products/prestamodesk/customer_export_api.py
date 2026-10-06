"""Bounded, tenant-scoped portable records from one database snapshot."""
import csv
import hashlib
import io
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.admin import add_admin_audit
from app.database import Base, get_db
from app.models import AdminAuditLog, Tenant, TenantMembership, User, UserInvitation
from app.products.prestamodesk.authorization import require_prestamodesk_administrator
from app.tenant_context import get_current_tenant

router = APIRouter(prefix="/administration", tags=["PréstamoDesk Export"])
MAX_ROWS = 50000
MAX_BYTES = 32 * 1024 * 1024
AUDIT_ACTIONS = (
    "client_team.role_changed", "client_team.member_removed", "client_team.status_changed", "client_team.profile_changed", "client_team.password_reset_requested",
    "client_user.invitation_created", "client_user.invitation_revoked", "client_user.invitation_accepted",
    "collections.assignment_created", "collections.assignment_released", "payments.voided", "customer_data.exported",
)


def portable(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: portable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [portable(item) for item in value]
    return value


def csv_cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, str) and (value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))):
        return "'" + value
    return value


def export_snapshot(connection, tenant_id, actor_id):
    # Authentication is checked again inside the same snapshot as the records.
    access = connection.execute(select(TenantMembership.id).join(User, User.id == TenantMembership.user_id)
        .join(Tenant, Tenant.id == TenantMembership.tenant_id).where(
            TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == actor_id,
            TenantMembership.role.in_(("owner", "administrator")), TenantMembership.is_active.is_(True),
            User.is_active.is_(True), Tenant.status == "active")).first()
    if access is None:
        raise HTTPException(status_code=403, detail="Administration access required")
    datasets = []
    for name, table in sorted(Base.metadata.tables.items()):
        if name.startswith("prestamodesk_"):
            if "tenant_id" not in table.c:
                raise RuntimeError("Product table has no tenant scope")
            datasets.append((name.removeprefix("prestamodesk_"), list(table.c), table.c.tenant_id == tenant_id))
    datasets.extend([
        ("tenant", list(Tenant.__table__.c), Tenant.id == tenant_id),
        ("memberships", list(TenantMembership.__table__.c), TenantMembership.tenant_id == tenant_id),
        ("team", [User.id, User.email, User.display_name, User.is_active, User.created_at],
         User.id.in_(select(TenantMembership.user_id).where(TenantMembership.tenant_id == tenant_id))),
        ("invitations", [c for c in UserInvitation.__table__.c if c.name != "token_hash"], UserInvitation.tenant_id == tenant_id),
        ("audit_history", list(AdminAuditLog.__table__.c),
         (AdminAuditLog.tenant_id == tenant_id) & AdminAuditLog.action.in_(AUDIT_ACTIONS)),
    ])
    output = {}; total = 0
    for name, columns, scope in datasets:
        table = columns[0].table
        rows = connection.execute(select(*columns).where(scope).order_by(table.c.id).limit(MAX_ROWS - total + 1)).mappings().all()
        total += len(rows)
        if total > MAX_ROWS:
            raise HTTPException(status_code=413, detail="Export exceeds self-service limit; request an assisted export")
        output[name] = {"columns": [c.name for c in columns], "rows": [portable(dict(row)) for row in rows]}
    return output


def create_archive(datasets, tenant_id, actor_id):
    now = datetime.now(timezone.utc)
    files = {}; size = 0
    def add(name, data):
        nonlocal size
        size += len(data)
        if size > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Export exceeds self-service limit; request an assisted export")
        files[name] = data
    records = {name: data["rows"] for name, data in datasets.items()}
    add("records.json", json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8"))
    for name, data in datasets.items():
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(data["columns"])
        for row in data["rows"]:
            writer.writerow([csv_cell(row.get(column)) for column in data["columns"]])
        add(name + ".csv", buffer.getvalue().encode("utf-8-sig"))
    manifest = {"format_version": 1, "product": "prestamodesk", "tenant_id": tenant_id,
                "exported_by_user_id": actor_id, "generated_at": now.isoformat(),
                "row_counts": {name: len(data["rows"]) for name, data in datasets.items()},
                "files": {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in files.items()},
                "notes": ["Decimal amounts are strings; date/time values preserve stored ISO representations.",
                          "CSV text that could be interpreted as a formula is prefixed with an apostrophe. JSON preserves original text.",
                          "Passwords, authentication tokens and platform billing records are excluded.",
                          "Audit includes tenant team, invitation, collection assignment, payment void and export events.",
                          "This export event is recorded after the snapshot and is not included in this archive.",
                          "This is a portable data export, not a database backup or an import format."]}
    add("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue(), manifest


@router.post("/export.zip")
def export_customer_data(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),
                         actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    engine = db.get_bind()
    # Separate transaction: request dependencies have already read from db.
    with engine.connect() as connection:
        if connection.dialect.name == "postgresql":
            connection = connection.execution_options(isolation_level="REPEATABLE READ")
        with connection.begin():
            if connection.dialect.name == "postgresql":
                connection.execute(text("SET TRANSACTION READ ONLY"))
            datasets = export_snapshot(connection, tenant.id, actor.user_id)
            archive, manifest = create_archive(datasets, tenant.id, actor.user_id)
    add_admin_audit(db, operator_user_id=actor.user_id, action="customer_data.exported", target_type="tenant",
                    target_id=tenant.id, tenant_id=tenant.id, after_data={"format_version": 1, "row_counts": manifest["row_counts"]})
    db.commit()
    filename = f"prestamodesk-cliente-{tenant.id}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.zip"
    return Response(archive, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff"})

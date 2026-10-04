"""Shared locking and snapshots for payment creation, closing and correction."""
from fastapi import HTTPException
from sqlalchemy import select

from app.models import Tenant, User

MONEY_FIELDS = ("principal_paid", "interest_paid", "late_fee_paid", "paid_amount", "late_fee_accrued")


def installment_snapshot(installment):
    return {
        **{name: str(getattr(installment, name)) for name in MONEY_FIELDS},
        "status": installment.status,
        "late_fee_assessed_through": (
            installment.late_fee_assessed_through.isoformat()
            if installment.late_fee_assessed_through else None
        ),
    }


def lock_financial_actor(db, tenant, membership, roles):
    # One tenant lock gives payments, role updates, voids and cash closings
    # a consistent lock order. This is intentionally conservative for the pilot.
    db.scalar(select(Tenant).where(Tenant.id == tenant.id).with_for_update())
    db.refresh(tenant)
    db.refresh(membership)
    active_user = db.scalar(select(User.is_active).where(User.id == membership.user_id))
    if tenant.status != "active" or not active_user or not membership.is_active or membership.role not in roles:
        raise HTTPException(status_code=403, detail="Payment operation access required")

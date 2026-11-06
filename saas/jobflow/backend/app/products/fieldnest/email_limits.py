"""Persistent rolling send budgets. SMTP attempts, including failures, count."""
from dataclasses import dataclass
from datetime import timedelta
from hashlib import sha256

from sqlalchemy import delete, func, select

from app.models import Product
from app.products.fieldnest.models.email_attempt import FieldNestEmailAttempt


@dataclass(frozen=True)
class EmailLimits:
    receipt_hour: int = 3
    receipt_day: int = 10
    recipient_hour: int = 30
    recipient_day: int = 100
    tenant_hour: int = 100
    tenant_day: int = 500
    platform_hour: int = 300
    platform_day: int = 1500
    tenant_pending: int = 200


EMAIL_LIMITS = EmailLimits()


def lock_email_delivery(db):
    # All dispatchers lock the same existing product row before checking budgets
    # and retain it through SMTP and commit. Intake does not take this lock.
    if db.scalar(select(Product.id).where(Product.slug == "fieldnest").with_for_update(key_share=True)) is None:
        raise RuntimeError("FieldNest delivery product unavailable")


def reserve_email_attempt(db, row, message, now):
    """Caller holds the delivery lock. Return a safe suppression code or None."""
    addresses = message["To"].addresses
    if len(addresses) != 1 or not addresses[0].username or not addresses[0].domain:
        raise ValueError("One email recipient required")
    recipient_hash = sha256(addresses[0].addr_spec.strip().casefold().encode()).hexdigest()
    attempt = FieldNestEmailAttempt
    # Keep more than the longest rolling window. No raw addresses/report text.
    db.execute(delete(attempt).where(attempt.attempted_at <= now - timedelta(days=2)))
    limits = EMAIL_LIMITS
    scopes = [
        ("Platform", (), limits.platform_hour, limits.platform_day),
        ("Tenant", (attempt.tenant_id == row.tenant_id,), limits.tenant_hour, limits.tenant_day),
        ("Recipient", (attempt.recipient_hash == recipient_hash,), limits.recipient_hour, limits.recipient_day),
    ]
    if row.kind == "receipt":
        scopes.append(("ReceiptRecipient", (attempt.recipient_hash == recipient_hash,
                                           attempt.kind == "receipt"),
                       limits.receipt_hour, limits.receipt_day))
    for scope, filters, hourly, daily in scopes:
        for period, duration, maximum in (
            ("Hour", timedelta(hours=1), hourly), ("Day", timedelta(days=1), daily),
        ):
            used = db.scalar(select(func.count()).select_from(attempt).where(
                attempt.attempted_at > now - duration, *filters,
            ))
            if used >= maximum:
                return f"{scope}{period}Limit"
    db.add(attempt(
        tenant_id=row.tenant_id, notification_id=row.id,
        recipient_hash=recipient_hash, kind=row.kind, attempted_at=now,
    ))
    # Fail closed before SMTP if history cannot be recorded.
    db.flush()
    return None

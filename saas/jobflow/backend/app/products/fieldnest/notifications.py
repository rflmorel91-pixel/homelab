"""Transactional outbox. SMTP is at-least-once; a stable Message-ID helps identify retries."""
import asyncio
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from hashlib import sha256
import logging
import os
import smtplib
import ssl
from urllib.parse import urlsplit

from sqlalchemy import select, func

from app.database import SessionLocal
from app.models import Tenant, TenantMembership, User, Product
from app.platform_email import smtp_config
from app.products.fieldnest.models.notification import FieldNestNotification
from app.products.fieldnest.models.property import FieldNestProperty
from app.products.fieldnest.models.work_order import FieldNestWorkOrder

log = logging.getLogger(__name__)
MAX_ATTEMPTS = 5


def queue_request_notifications(db, order, receipt_email=None):
    owners = db.scalars(select(User.id).join(
        TenantMembership, TenantMembership.user_id == User.id
    ).where(
        TenantMembership.tenant_id == order.tenant_id,
        TenantMembership.role == "owner", TenantMembership.is_active.is_(True),
        User.is_active.is_(True),
    )).all()
    recipients = [("owner", user_id, None) for user_id in owners]
    if receipt_email:
        recipients.append(("receipt", None, receipt_email))
    for kind, user_id, email in recipients:
        key = sha256(f"{order.id}:{kind}:{user_id or email}".encode()).hexdigest()
        db.add(FieldNestNotification(
            tenant_id=order.tenant_id, work_order_id=order.id,
            owner_user_id=user_id, receipt_email=email, kind=kind, event_key=key,
        ))


def workspace_url(tenant_id):
    base = os.getenv("PLATFORM_PUBLIC_BASE_URL", "").rstrip("/")
    parsed = urlsplit(base)
    local = parsed.hostname in {"localhost", "127.0.0.1"}
    if (parsed.scheme != "https" and not (local and parsed.scheme == "http")) or not parsed.netloc:
        return None
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None
    return base + f"/fieldnest/workspace?company={tenant_id}#work-orders"


def make_message(db, row, config):
    tenant = db.scalar(select(Tenant).join(Product).where(
        Tenant.id == row.tenant_id, Tenant.status == "active",
        Product.slug == "fieldnest", Product.status == "active",
    ))
    order = db.scalar(select(FieldNestWorkOrder).where(
        FieldNestWorkOrder.id == row.work_order_id,
        FieldNestWorkOrder.tenant_id == row.tenant_id,
    ))
    if tenant is None or order is None:
        return None
    message = EmailMessage()
    message["From"] = str(config["from_email"])
    message["Message-ID"] = f"<fieldnest-{row.event_key}@notifications.fieldlookers.invalid>"
    reference = f"FN-{order.id}"
    if row.kind == "owner":
        # Recheck access immediately before delivery. Do not notify former owners.
        owner = db.scalar(select(User).join(TenantMembership).where(
            User.id == row.owner_user_id, User.is_active.is_(True),
            TenantMembership.tenant_id == row.tenant_id,
            TenantMembership.role == "owner", TenantMembership.is_active.is_(True),
        ))
        if owner is None:
            return None
        prop = db.scalar(select(FieldNestProperty).where(
            FieldNestProperty.id == order.property_id,
            FieldNestProperty.tenant_id == row.tenant_id,
        ))
        if prop is None:
            return None
        message["To"] = owner.email
        message["Subject"] = f"FieldNest: new maintenance request {reference}"
        lines = [
            "A resident submitted a maintenance request.",
            "", f"Reference: {reference}", f"Property: {prop.name}",
            "", "Sign in to your FieldNest workspace to review the issue and coordinate the next step.",
        ]
        if workspace_url(row.tenant_id):
            lines.extend(["", workspace_url(row.tenant_id)])
    elif row.kind == "receipt" and row.receipt_email:
        message["To"] = row.receipt_email
        message["Subject"] = f"FieldNest: maintenance report received {reference}"
        # Fixed content: do not repeat unverified submitter text or expose private details.
        lines = [
            "Your maintenance report was received.", "", f"Reference: {reference}",
            "", "The property team can review the report and coordinate the next step.",
            "This confirms receipt, not a scheduled repair or permission to enter.",
            "", "For emergencies, use emergency services or your property's emergency contact.",
            "Do not reply to this automated receipt. Contact your property manager directly.",
            "If you did not submit a report, you can ignore this message.",
        ]
    else:
        return None
    message.set_content("\n".join(lines))
    return message


def send_message(message, config):
    with smtplib.SMTP(str(config["host"]), int(config["port"]), timeout=15) as smtp:
        if config["use_tls"]:
            smtp.starttls(context=ssl.create_default_context())
        if config["username"]:
            if not config["password"]:
                raise RuntimeError("SMTP password is required")
            smtp.login(str(config["username"]), str(config["password"]))
        smtp.send_message(message)


def deliver_one(session_factory=SessionLocal, sender=send_message, config_factory=smtp_config):
    """Lock one due row; parallel API workers skip rows already being delivered."""
    with session_factory() as db:
        row = db.scalar(select(FieldNestNotification).where(
            FieldNestNotification.status == "pending",
            FieldNestNotification.available_at <= datetime.now(timezone.utc),
        ).order_by(FieldNestNotification.id).with_for_update(skip_locked=True).limit(1))
        if row is None:
            return False
        row.attempts += 1
        try:
            config = config_factory()
            message = make_message(db, row, config)
            if message is None:
                row.status = "skipped"
                row.last_error = "RecipientOrWorkspaceUnavailable"
            else:
                sender(message, config)
                row.status = "sent"
                row.sent_at = datetime.now(timezone.utc)
                row.last_error = None
        except Exception as error:
            # Configuration failures count too. Never store SMTP exception text or credentials.
            row.last_error = type(error).__name__[:80]
            if row.attempts >= MAX_ATTEMPTS:
                row.status = "failed"
            else:
                row.available_at = datetime.now(timezone.utc) + timedelta(seconds=min(60 * 2 ** (row.attempts - 1), 900))
        db.commit()
        return True


async def notification_loop(stop):
    while not stop.is_set():
        try:
            delivered = await asyncio.to_thread(deliver_one)
        except Exception:
            # A temporary DB problem must not take down the API or log report contents.
            log.warning("FieldNest email dispatcher temporarily unavailable")
            delivered = False
        try:
            await asyncio.wait_for(stop.wait(), timeout=0.25 if delivered else 5)
        except TimeoutError:
            pass


def notification_counts(db):
    return dict(db.execute(select(
        FieldNestNotification.status, func.count()
    ).group_by(FieldNestNotification.status)).all())

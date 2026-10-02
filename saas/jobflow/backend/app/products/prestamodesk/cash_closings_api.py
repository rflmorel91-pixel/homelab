from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.cash_closing_schemas import (
    CashClosingCreate,
    CashClosingPreview,
    CashClosingRead,
)
from app.products.prestamodesk.models import (
    CashClosing,
    Payment,
)
from app.tenant_context import (
    get_current_tenant,
    get_current_tenant_membership,
)


router = APIRouter(
    prefix="/cashier",
    tags=["PréstamoDesk Cash Closing"],
)


def require_cashier(
    membership: TenantMembership,
) -> None:
    if membership.role != "member":
        raise HTTPException(
            status_code=403,
            detail="Cashier membership required",
        )


def unclosed_payments_statement(
    *,
    tenant_id: int,
    user_id: int,
):
    return (
        select(Payment)
        .where(
            Payment.tenant_id == tenant_id,
            Payment.recorded_by_user_id == user_id,
            Payment.cash_closing_id.is_(None),
        )
        .order_by(Payment.created_at, Payment.id)
    )


def totals_for(
    payments: list[Payment],
) -> dict[str, Decimal]:
    zero = Decimal("0.00")

    def total(method: str) -> Decimal:
        return money(
            sum(
                (
                    payment.amount
                    for payment in payments
                    if payment.payment_method == method
                ),
                zero,
            )
        )

    return {
        "total_collected": money(
            sum(
                (payment.amount for payment in payments),
                zero,
            )
        ),
        "cash_expected": total("cash"),
        "bank_transfer_total": total(
            "bank_transfer"
        ),
        "card_total": total("card"),
        "other_total": total("other"),
    }


def opened_at_for(
    *,
    db: Session,
    tenant_id: int,
    user_id: int,
    payments: list[Payment],
    closed_at: datetime,
) -> datetime:
    previous = db.scalar(
        select(CashClosing)
        .where(
            CashClosing.tenant_id == tenant_id,
            CashClosing.cashier_user_id == user_id,
        )
        .order_by(
            CashClosing.closed_at.desc(),
            CashClosing.id.desc(),
        )
        .limit(1)
    )

    if previous is not None:
        return previous.closed_at

    if payments:
        return payments[0].created_at

    return closed_at


def preview_for(
    *,
    db: Session,
    tenant_id: int,
    user_id: int,
) -> CashClosingPreview:
    payments = list(
        db.scalars(
            unclosed_payments_statement(
                tenant_id=tenant_id,
                user_id=user_id,
            )
        ).all()
    )
    now = datetime.now(timezone.utc)
    totals = totals_for(payments)

    return CashClosingPreview(
        opened_at=opened_at_for(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            payments=payments,
            closed_at=now,
        ),
        payment_count=len(payments),
        **totals,
    )


@router.get(
    "/closing-preview",
    response_model=CashClosingPreview,
)
def get_closing_preview(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_cashier(membership)

    return preview_for(
        db=db,
        tenant_id=tenant.id,
        user_id=membership.user_id,
    )


@router.post(
    "/closings",
    response_model=CashClosingRead,
    status_code=201,
)
def close_cashier_register(
    payload: CashClosingCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_cashier(membership)

    db.scalar(
        select(TenantMembership)
        .where(
            TenantMembership.id == membership.id,
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id
            == membership.user_id,
        )
        .with_for_update()
    )

    payments = list(
        db.scalars(
            unclosed_payments_statement(
                tenant_id=tenant.id,
                user_id=membership.user_id,
            )
            .with_for_update()
        ).all()
    )

    closed_at = datetime.now(timezone.utc)
    totals = totals_for(payments)
    cash_counted = money(payload.cash_counted)

    closing = CashClosing(
        tenant_id=tenant.id,
        cashier_user_id=membership.user_id,
        opened_at=opened_at_for(
            db=db,
            tenant_id=tenant.id,
            user_id=membership.user_id,
            payments=payments,
            closed_at=closed_at,
        ),
        closed_at=closed_at,
        payment_count=len(payments),
        cash_counted=cash_counted,
        cash_difference=money(
            cash_counted
            - totals["cash_expected"]
        ),
        notes=payload.notes,
        **totals,
    )

    try:
        db.add(closing)
        db.flush()

        for payment in payments:
            payment.cash_closing_id = closing.id

        db.commit()
        db.refresh(closing)
    except Exception:
        db.rollback()
        raise

    return CashClosingRead.model_validate(closing)


@router.get(
    "/closings",
    response_model=list[CashClosingRead],
)
def list_cashier_closings(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_cashier(membership)

    return list(
        db.scalars(
            select(CashClosing)
            .where(
                CashClosing.tenant_id == tenant.id,
                CashClosing.cashier_user_id
                == membership.user_id,
            )
            .order_by(
                CashClosing.closed_at.desc(),
                CashClosing.id.desc(),
            )
        ).all()
    )

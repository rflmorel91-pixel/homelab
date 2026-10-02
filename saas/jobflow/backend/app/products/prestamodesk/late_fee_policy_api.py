from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.prestamodesk.authorization import (
    require_prestamodesk_operations_member,
)
from app.products.prestamodesk.late_fee_schemas import (
    LateFeePolicyRead,
    LateFeePolicyUpdate,
)
from app.products.prestamodesk.models import LateFeePolicy
from app.tenant_context import (
    get_current_tenant,
    require_current_tenant_owner,
)


router = APIRouter(
    prefix="/late-fee-policy",
    tags=["PréstamoDesk Late Fees"],
    dependencies=[
        Depends(
            require_prestamodesk_operations_member
        ),
        Depends(require_current_tenant_owner),
    ],
)


def get_policy(
    db: Session,
    tenant_id: int,
) -> LateFeePolicy | None:
    return db.scalar(
        select(LateFeePolicy).where(
            LateFeePolicy.tenant_id == tenant_id
        )
    )


@router.get("", response_model=LateFeePolicyRead)
def read_late_fee_policy(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    policy = get_policy(db, tenant.id)

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail="Late-fee policy not configured",
        )

    return policy


@router.put("", response_model=LateFeePolicyRead)
def configure_late_fee_policy(
    payload: LateFeePolicyUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    policy = get_policy(db, tenant.id)

    if policy is None:
        policy = LateFeePolicy(
            tenant_id=tenant.id,
            **payload.model_dump(),
        )
        db.add(policy)
    else:
        for field, value in payload.model_dump().items():
            setattr(policy, field, value)

    db.commit()
    db.refresh(policy)

    return policy

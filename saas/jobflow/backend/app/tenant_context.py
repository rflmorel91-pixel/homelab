from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant


def get_current_tenant(
    x_tenant_id: int | None = Header(
        default=None,
        alias="X-Tenant-ID",
    ),
    db: Session = Depends(get_db),
) -> Tenant:
    if x_tenant_id is None:
        raise HTTPException(
            status_code=401,
            detail="Tenant context required",
        )

    tenant = db.get(Tenant, x_tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return tenant

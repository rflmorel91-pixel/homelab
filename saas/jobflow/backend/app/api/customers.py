from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Job, Tenant
from app.schemas import CustomerCreate, CustomerRead, CustomerUpdate
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post("/", response_model=CustomerRead, status_code=201)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_customer = Customer(
        tenant_id=tenant.id,
        **customer.model_dump(),
    )

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)

    return db_customer


@router.get("/", response_model=list[CustomerRead])
def list_customers(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Customer)
        .where(Customer.tenant_id == tenant.id)
        .order_by(Customer.id)
    )

    return result.scalars().all()


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    customer: CustomerUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    for field, value in customer.model_dump().items():
        setattr(db_customer, field, value)

    db.commit()
    db.refresh(db_customer)

    return db_customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    existing_job = db.execute(
        select(Job.id).where(
            Job.customer_id == customer_id
        ).limit(1)
    ).scalar_one_or_none()

    if existing_job is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete customer with existing jobs",
        )

    db.delete(db_customer)
    db.commit()

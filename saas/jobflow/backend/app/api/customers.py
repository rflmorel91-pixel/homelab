from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer
from app.schemas import CustomerCreate, CustomerRead, CustomerUpdate


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post("/", response_model=CustomerRead, status_code=201)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    db_customer = Customer(**customer.model_dump())

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)

    return db_customer


@router.get("/", response_model=list[CustomerRead])
def list_customers(
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(Customer).order_by(Customer.id)
    )

    return result.scalars().all()


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)

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
):
    db_customer = db.get(Customer, customer_id)

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
):
    db_customer = db.get(Customer, customer_id)

    if db_customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    db.delete(db_customer)
    db.commit()

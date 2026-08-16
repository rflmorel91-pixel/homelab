from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invoice, Job, Payment
from app.schemas import PaymentCreate, PaymentRead, PaymentUpdate


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post("/", response_model=PaymentRead, status_code=201)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
):
    invoice = db.get(Invoice, payment.invoice_id)

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    existing_total = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.invoice_id == invoice.id)
    )

    new_total = existing_total + payment.amount

    if new_total > invoice.amount:
        raise HTTPException(
            status_code=400,
            detail="Payment exceeds remaining invoice balance",
        )

    db_payment = Payment(**payment.model_dump())

    db.add(db_payment)

    if new_total == invoice.amount and invoice.status == "sent":
        invoice.status = "paid"

        job = db.get(Job, invoice.job_id)

        if job is not None and job.status == "invoiced":
            job.status = "paid"

    db.commit()
    db.refresh(db_payment)

    return db_payment


@router.get("/", response_model=list[PaymentRead])
def list_payments(
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(Payment).order_by(Payment.id)
    )

    return result.scalars().all()


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    payment = db.get(Payment, payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


@router.put("/{payment_id}", response_model=PaymentRead)
def update_payment(
    payment_id: int,
    payment: PaymentUpdate,
    db: Session = Depends(get_db),
):
    db_payment = db.get(Payment, payment_id)

    if db_payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.invoice_id != db_payment.invoice_id:
        invoice = db.get(Invoice, payment.invoice_id)

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found",
            )

    for field, value in payment.model_dump().items():
        setattr(db_payment, field, value)

    db.commit()
    db.refresh(db_payment)

    return db_payment


@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    db_payment = db.get(Payment, payment_id)

    if db_payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    db.delete(db_payment)
    db.commit()

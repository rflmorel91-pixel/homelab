from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.jobflow.models import (
    Customer,
    Invoice,
    Job,
    Payment,
)
from app.products.jobflow.schemas import PaymentCreate, PaymentRead, PaymentUpdate
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)



def sync_job_payment_status(
    job: Job,
    db: Session,
) -> None:
    db.flush()

    invoices = db.execute(
        select(Invoice).where(Invoice.job_id == job.id)
    ).scalars().all()

    all_invoices_paid = (
        bool(invoices)
        and all(invoice.status == "paid" for invoice in invoices)
    )

    if all_invoices_paid and job.status == "invoiced":
        job.status = "paid"

    elif not all_invoices_paid and job.status == "paid":
        job.status = "invoiced"


def sync_invoice_payment_status(
    invoice: Invoice,
    db: Session,
) -> None:
    total_paid = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.invoice_id == invoice.id)
    )

    if total_paid == invoice.amount:
        if invoice.status == "sent":
            invoice.status = "paid"

    elif total_paid < invoice.amount:
        if invoice.status == "paid":
            invoice.status = "sent"

    job = db.get(Job, invoice.job_id)

    if job is not None:
        sync_job_payment_status(job, db)


@router.post("/", response_model=PaymentRead, status_code=201)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    invoice = db.scalar(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Invoice.id == payment.invoice_id,
            Customer.tenant_id == tenant.id,
        )
    )

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
    db.flush()

    sync_invoice_payment_status(invoice, db)

    db.commit()
    db.refresh(db_payment)

    return db_payment


@router.get("/", response_model=list[PaymentRead])
def list_payments(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Payment)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(Customer.tenant_id == tenant.id)
        .order_by(Payment.id)
    )

    return result.scalars().all()


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    payment = db.scalar(
        select(Payment)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Payment.id == payment_id,
            Customer.tenant_id == tenant.id,
        )
    )

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
    tenant: Tenant = Depends(get_current_tenant),
):
    db_payment = db.scalar(
        select(Payment)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Payment.id == payment_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    old_invoice = db.scalar(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Invoice.id == db_payment.invoice_id,
            Customer.tenant_id == tenant.id,
        )
    )

    new_invoice = db.scalar(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Invoice.id == payment.invoice_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if new_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    existing_total = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(
            Payment.invoice_id == payment.invoice_id,
            Payment.id != payment_id,
        )
    )

    new_total = existing_total + payment.amount

    if new_total > new_invoice.amount:
        raise HTTPException(
            status_code=400,
            detail="Payment exceeds remaining invoice balance",
        )

    for field, value in payment.model_dump().items():
        setattr(db_payment, field, value)

    db.flush()

    if old_invoice is not None:
        sync_invoice_payment_status(old_invoice, db)

    if (
        old_invoice is None
        or new_invoice.id != old_invoice.id
    ):
        sync_invoice_payment_status(new_invoice, db)
    else:
        sync_invoice_payment_status(new_invoice, db)

    db.commit()
    db.refresh(db_payment)

    return db_payment


@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_payment = db.scalar(
        select(Payment)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Payment.id == payment_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    invoice = db.scalar(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Invoice.id == db_payment.invoice_id,
            Customer.tenant_id == tenant.id,
        )
    )

    db.delete(db_payment)
    db.flush()

    if invoice is not None:
        sync_invoice_payment_status(invoice, db)

    db.commit()

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
from app.products.jobflow.schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate
from app.tenant_context import get_current_tenant


INVOICE_STATUS_TRANSITIONS = {
    "draft": {"sent"},
    "sent": {"paid"},
    "paid": set(),
}


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)


@router.post("/", response_model=InvoiceRead, status_code=201)
def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    job = db.scalar(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Job.id == invoice.job_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    db_invoice = Invoice(**invoice.model_dump())

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    return db_invoice


@router.get("/", response_model=list[InvoiceRead])
def list_invoices(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(Customer.tenant_id == tenant.id)
        .order_by(Invoice.id)
    )

    return result.scalars().all()


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    invoice = db.scalar(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Invoice.id == invoice_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    return invoice


@router.put("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(
    invoice_id: int,
    invoice: InvoiceUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_invoice = db.scalar(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Invoice.id == invoice_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    if invoice.job_id != db_invoice.job_id:
        raise HTTPException(
            status_code=409,
            detail="Invoice cannot be moved to a different job",
        )

    total_paid = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.invoice_id == invoice_id)
    )

    if (
        db_invoice.status == "paid"
        and invoice.amount != db_invoice.amount
    ):
        raise HTTPException(
            status_code=409,
            detail="Paid invoice amount cannot be changed",
        )

    if invoice.amount < total_paid:
        raise HTTPException(
            status_code=409,
            detail="Invoice amount cannot be less than existing payments",
        )

    previous_status = db_invoice.status

    if invoice.status != previous_status:
        allowed_statuses = INVOICE_STATUS_TRANSITIONS.get(
            previous_status,
            set(),
        )

        if invoice.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid invoice status transition: "
                    f"{previous_status} -> {invoice.status}"
                ),
            )

    for field, value in invoice.model_dump().items():
        setattr(db_invoice, field, value)

    if (
        previous_status == "draft"
        and invoice.status == "sent"
    ):
        job = db.scalar(
            select(Job)
            .join(Customer, Customer.id == Job.customer_id)
            .where(
                Job.id == db_invoice.job_id,
                Customer.tenant_id == tenant.id,
            )
        )

        if job is not None and job.status == "completed":
            job.status = "invoiced"

    db.commit()
    db.refresh(db_invoice)

    return db_invoice


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_invoice = db.scalar(
        select(Invoice)
        .join(Job, Job.id == Invoice.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Invoice.id == invoice_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    payment = db.scalar(
        select(Payment)
        .where(Payment.invoice_id == invoice_id)
        .limit(1)
    )

    if payment is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete invoice with existing payments",
        )

    db.delete(db_invoice)
    db.commit()

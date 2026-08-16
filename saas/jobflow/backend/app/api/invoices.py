from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invoice, Job, Payment
from app.schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate


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
):
    job = db.get(Job, invoice.job_id)

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
):
    result = db.execute(
        select(Invoice).order_by(Invoice.id)
    )

    return result.scalars().all()


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    invoice = db.get(Invoice, invoice_id)

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
):
    db_invoice = db.get(Invoice, invoice_id)

    if db_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    if invoice.job_id != db_invoice.job_id:
        job = db.get(Job, invoice.job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
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
        job = db.get(Job, db_invoice.job_id)

        if job is not None and job.status == "completed":
            job.status = "invoiced"

    db.commit()
    db.refresh(db_invoice)

    return db_invoice


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    db_invoice = db.get(Invoice, invoice_id)

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

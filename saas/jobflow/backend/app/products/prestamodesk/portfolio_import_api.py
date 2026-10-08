"""Bounded CSV preview and atomic, replay-safe opening-balance imports."""
import csv
import hashlib
import io
import json
import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.admin import add_admin_audit
from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.amortization import build_fixed_schedule, money
from app.products.prestamodesk.authorization import require_prestamodesk_administrator
from app.products.prestamodesk.models import Borrower, Installment, Loan
from app.products.prestamodesk.models.portfolio_import import ImportedLoan, PortfolioImport
from app.products.prestamodesk.payment_corrections import lock_financial_actor
from app.tenant_context import get_current_tenant

router = APIRouter(prefix="/administration/imports", tags=["PréstamoDesk Portfolio Import"],
                   dependencies=[Depends(require_prestamodesk_administrator)])
COLUMNS = "referencia,nombre,tipo_documento,documento,telefono,tipo_prestamo,fecha_inicio,primera_cuota,frecuencia,capital_original,interes_porcentaje,numero_cuotas,cuota,vencimiento,capital_cuota,interes_cuota,capital_pagado,interes_pagado,mora_pendiente,saldo_pendiente".split(",")
MAX_ROWS = 500
Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    csv_text: str = Field(min_length=1, max_length=1_000_000)
    cutoff_date: date


class ImportCommit(ImportRequest):
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirm_balances: Literal[True]


class ImportRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    referencia: str = Field(min_length=1, max_length=100)
    nombre: str = Field(min_length=1, max_length=200)
    tipo_documento: Literal["cedula", "passport", "other"]
    documento: str = Field(min_length=1, max_length=50)
    telefono: str = Field(max_length=40)
    tipo_prestamo: Literal["personal"]
    fecha_inicio: date
    primera_cuota: date
    frecuencia: Literal["daily", "weekly", "biweekly", "monthly"]
    capital_original: Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]
    interes_porcentaje: Annotated[Decimal, Field(ge=0, le=999, max_digits=7, decimal_places=4)]
    numero_cuotas: int = Field(ge=1, le=360)
    cuota: int = Field(ge=1, le=360)
    vencimiento: date
    capital_cuota: Money
    interes_cuota: Money
    capital_pagado: Money
    interes_pagado: Money
    mora_pendiente: Money
    saldo_pendiente: Money


def document_key(value):
    return re.sub(r"[\s-]", "", value).casefold()


def parse_rows(payload):
    today = datetime.now(ZoneInfo("America/Santo_Domingo")).date()
    if payload.cutoff_date > today:
        raise HTTPException(422, "La fecha de corte no puede ser futura.")
    if len(payload.csv_text.encode("utf-8")) > 1_000_000:
        raise HTTPException(422, "El CSV supera 1 MB.")
    reader = csv.DictReader(io.StringIO(payload.csv_text.lstrip("\ufeff")), strict=True)
    try:
        if reader.fieldnames != COLUMNS:
            raise HTTPException(422, "Utilice las columnas y el orden de la plantilla CSV.")
        rows, errors = [], []
        for index, raw in enumerate(reader, 2):
            if index > MAX_ROWS + 1:
                raise HTTPException(422, "Máximo 500 filas de cuotas por importación.")
            try:
                if None in raw or any(value is None for value in raw.values()):
                    raise ValueError("Cantidad de columnas incorrecta.")
                data = {key: value.strip() for key, value in raw.items()}
                row = ImportRow.model_validate(data)
                if row.referencia.startswith(("=", "+", "-", "@")):
                    raise ValueError("La referencia debe ser texto simple.")
                if not document_key(row.documento):
                    raise ValueError("Documento vacío.")
                if row.fecha_inicio > payload.cutoff_date or row.primera_cuota < row.fecha_inicio:
                    raise ValueError("Revise la fecha de inicio y la primera cuota.")
                if row.mora_pendiente != 0:
                    raise ValueError("Esta versión no importa mora; concilie el préstamo antes de importar.")
                rows.append((index, row))
            except ValidationError as error:
                fields = ", ".join(str(item["loc"][0]) for item in error.errors())
                errors.append({"row": index, "message": "Revise campos: " + fields})
            except ValueError as error:
                errors.append({"row": index, "message": str(error)})
    except csv.Error:
        raise HTTPException(422, "CSV inválido.")
    if not rows and not errors:
        raise HTTPException(422, "El archivo no contiene cuotas.")
    return rows, errors


def preview_data(payload, db, tenant_id):
    rows, errors = parse_rows(payload)
    grouped = defaultdict(list)
    for index, row in rows:
        grouped[row.referencia].append((index, row))
    if len(grouped) > 100:
        raise HTTPException(422, "Máximo 100 préstamos por importación.")
    existing = db.scalars(select(Borrower).where(Borrower.tenant_id == tenant_id).limit(50001)).all()
    if len(existing) > 50000:
        raise HTTPException(422, "La cartera requiere una importación asistida.")
    borrowers = defaultdict(list)
    for borrower in existing:
        if borrower.document_number:
            borrowers[document_key(borrower.document_number)].append(borrower)
    references = set(db.scalars(select(ImportedLoan.external_reference).where(
        ImportedLoan.tenant_id == tenant_id, ImportedLoan.external_reference.in_(grouped))).all())
    plans, summaries, people = [], [], {}
    for reference, entries in grouped.items():
        row_number, first = entries[0]
        try:
            if reference in references:
                raise ValueError("Referencia ya importada en este cliente.")
            metadata = first.model_dump(exclude={"cuota", "vencimiento", "capital_cuota", "interes_cuota", "capital_pagado", "interes_pagado", "mora_pendiente", "saldo_pendiente"})
            if any(row.model_dump(exclude={"cuota", "vencimiento", "capital_cuota", "interes_cuota", "capital_pagado", "interes_pagado", "mora_pendiente", "saldo_pendiente"}) != metadata for _, row in entries):
                raise ValueError("Los datos del préstamo deben coincidir en todas sus cuotas.")
            identity = document_key(first.documento)
            person = (first.nombre, first.tipo_documento, first.telefono)
            if identity in people and people[identity] != person:
                raise ValueError("El mismo documento tiene datos de prestatario diferentes.")
            people[identity] = person
            matches = borrowers.get(identity, [])
            if len(matches) > 1:
                raise ValueError("Documento ambiguo en la cartera existente.")
            borrower = matches[0] if matches else None
            if borrower and (borrower.status != "active" or borrower.full_name.strip() != first.nombre or borrower.document_type != first.tipo_documento):
                raise ValueError("El documento existente corresponde a datos diferentes o acceso inactivo.")
            ordered = sorted(entries, key=lambda item: item[1].cuota)
            if [row.cuota for _, row in ordered] != list(range(1, first.numero_cuotas + 1)):
                raise ValueError("Incluya todas las cuotas originales, una vez cada una, desde 1.")
            schedule = build_fixed_schedule(principal_amount=first.capital_original,
                flat_interest_rate_percent=first.interes_porcentaje, installment_count=first.numero_cuotas,
                payment_frequency=first.frecuencia, first_payment_date=first.primera_cuota)
            if schedule.total_due >= Decimal("1000000000000"):
                raise ValueError("El total del préstamo excede el límite.")
            paid = Decimal("0.00")
            balance = Decimal("0.00")
            for (number, row), expected in zip(ordered, schedule.installments):
                if row.vencimiento != expected.due_date:
                    raise ValueError(f"Fila {number}: vencimiento incompatible con el calendario.")
                if row.capital_cuota != expected.principal_due or row.interes_cuota != expected.interest_due:
                    raise ValueError(f"Fila {number}: capital o interés original no coincide con el cálculo fijo. No convierta el contrato para importar.")
                if row.capital_pagado > expected.principal_due or row.interes_pagado > expected.interest_due:
                    raise ValueError(f"Fila {number}: abonos superiores al capital o interés de la cuota.")
                due = money(expected.total_due - row.capital_pagado - row.interes_pagado)
                if due != row.saldo_pendiente:
                    raise ValueError(f"Fila {number}: saldo pendiente no coincide con capital e interés menos abonos.")
                paid += row.capital_pagado + row.interes_pagado
                balance += due
            if balance == 0:
                raise ValueError("Importe solo préstamos con saldo pendiente.")
            plans.append((first, ordered, schedule, borrower))
            summaries.append({"reference": reference, "borrower": first.nombre,
                "borrower_action": "Usar existente" if borrower else "Crear prestatario",
                "installments": first.numero_cuotas, "total_due": str(schedule.total_due),
                "historical_paid": str(money(paid)), "opening_balance": str(money(balance))})
        except (ValueError, OverflowError) as error:
            errors.append({"row": row_number, "reference": reference, "message": str(error)})
    canonical = {"cutoff_date": payload.cutoff_date.isoformat(),
                 "rows": sorted([row.model_dump(mode="json") for _, row in rows], key=lambda item: (item["referencia"], item["cuota"]))}
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    result = {"fingerprint": fingerprint, "cutoff_date": payload.cutoff_date.isoformat(),
        "valid": not errors, "errors": errors, "loans": summaries,
        "opening_balance": str(money(sum((Decimal(item["opening_balance"]) for item in summaries), Decimal("0")))),
        "historical_paid": str(money(sum((Decimal(item["historical_paid"]) for item in summaries), Decimal("0")))),
        "loan_count": len(summaries), "installment_count": len(rows)}
    return result, plans, canonical


@router.get("/template")
def template():
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(COLUMNS)
    writer.writerow(["EJEMPLO-001", "Ana Ejemplo", "cedula", "SYNTHETIC-001", "", "personal", "2026-09-01", "2026-10-01", "monthly", "10000.00", "10", "2", "1", "2026-10-01", "5000.00", "500.00", "1000.00", "100.00", "0.00", "4400.00"])
    writer.writerow(["EJEMPLO-001", "Ana Ejemplo", "cedula", "SYNTHETIC-001", "", "personal", "2026-09-01", "2026-10-01", "monthly", "10000.00", "10", "2", "2", "2026-11-01", "5000.00", "500.00", "0.00", "0.00", "0.00", "5500.00"])
    return Response("\ufeff" + stream.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="prestamodesk-import-template.csv"', "Cache-Control": "no-store"})


@router.post("/preview")
def preview(payload: ImportRequest, response: Response, db: Session = Depends(get_db),
            tenant: Tenant = Depends(get_current_tenant)):
    response.headers["Cache-Control"] = "no-store"
    return preview_data(payload, db, tenant.id)[0]


@router.post("", status_code=201)
def commit_import(payload: ImportCommit, response: Response, db: Session = Depends(get_db),
                  tenant: Tenant = Depends(get_current_tenant),
                  actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    response.headers["Cache-Control"] = "no-store"
    lock_financial_actor(db, tenant, actor, {"owner", "administrator"})
    previous = db.scalar(select(PortfolioImport).where(PortfolioImport.tenant_id == tenant.id,
                                                      PortfolioImport.fingerprint == payload.fingerprint))
    # Even retries must contain exactly the originally reviewed payload.
    rows, parse_errors = parse_rows(payload)
    canonical = {"cutoff_date": payload.cutoff_date.isoformat(), "rows": sorted(
        [row.model_dump(mode="json") for _, row in rows], key=lambda item: (item["referencia"], item["cuota"]))}
    actual = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if parse_errors or actual != payload.fingerprint:
        raise HTTPException(409, "El archivo cambió. Genere una nueva vista previa.")
    if previous:
        response.status_code = 200
        return {"import_id": previous.id, "replayed": True, "source": previous.snapshot["source"], **previous.snapshot["report"]}
    result, plans, canonical = preview_data(payload, db, tenant.id)
    if not result["valid"]:
        raise HTTPException(422, result)
    try:
        batch = PortfolioImport(tenant_id=tenant.id, actor_user_id=actor.user_id,
            cutoff_date=payload.cutoff_date, fingerprint=result["fingerprint"], snapshot={})
        db.add(batch)
        db.flush()
        created_people, mappings = {}, []
        for first, entries, schedule, borrower in plans:
            key = document_key(first.documento)
            borrower = borrower or created_people.get(key)
            if borrower is None:
                borrower = Borrower(tenant_id=tenant.id, full_name=first.nombre, document_type=first.tipo_documento,
                                    document_number=first.documento, phone=first.telefono or None, status="active")
                db.add(borrower)
                db.flush()
                created_people[key] = borrower
            loan = Loan(tenant_id=tenant.id, borrower_id=borrower.id, loan_type="personal",
                principal_amount=schedule.principal_amount, flat_interest_rate_percent=schedule.flat_interest_rate_percent,
                total_interest=schedule.total_interest, total_due=schedule.total_due, installment_count=first.numero_cuotas,
                payment_frequency=first.frecuencia, start_date=first.fecha_inicio, first_payment_date=first.primera_cuota,
                currency="DOP", status="active", late_fee_enabled=False,
                notes=f"Importación #{batch.id} · {first.referencia} · Corte {payload.cutoff_date.isoformat()}. Abonos anteriores son saldos iniciales, no cobros de Caja.")
            db.add(loan)
            db.flush()
            for (_, row), expected in zip(entries, schedule.installments):
                paid = money(row.capital_pagado + row.interes_pagado)
                status = "paid" if row.saldo_pendiente == 0 else "partial" if paid > 0 else "pending"
                db.add(Installment(tenant_id=tenant.id, loan_id=loan.id, sequence_number=row.cuota,
                    due_date=row.vencimiento, principal_due=expected.principal_due, interest_due=expected.interest_due,
                    total_due=expected.total_due, paid_amount=paid, principal_paid=row.capital_pagado,
                    interest_paid=row.interes_pagado, late_fee_accrued=0, late_fee_paid=0, status=status))
            db.add(ImportedLoan(tenant_id=tenant.id, import_id=batch.id, loan_id=loan.id, external_reference=first.referencia))
            mappings.append({"reference": first.referencia, "loan_id": loan.id, "borrower_id": borrower.id})
        result["records"] = mappings
        batch.snapshot = {"source": canonical, "report": result}
        add_admin_audit(db, operator_user_id=actor.user_id, action="portfolio.imported", target_type="portfolio_import",
                        target_id=batch.id, tenant_id=tenant.id, after_data={"fingerprint": batch.fingerprint,
                        "opening_balance": result["opening_balance"], "loan_count": result["loan_count"]})
        db.commit()
        return {"import_id": batch.id, "replayed": False, "source": canonical, **result}
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "La cartera cambió o la referencia ya existe. Revise de nuevo.")
    except Exception:
        db.rollback()
        raise


@router.get("/{import_id}")
def report(import_id: int, response: Response, db: Session = Depends(get_db),
           tenant: Tenant = Depends(get_current_tenant)):
    response.headers["Cache-Control"] = "no-store"
    batch = db.scalar(select(PortfolioImport).where(PortfolioImport.id == import_id, PortfolioImport.tenant_id == tenant.id))
    if batch is None:
        raise HTTPException(404, "Importación no encontrada.")
    return {"import_id": batch.id, "actor_user_id": batch.actor_user_id, "created_at": batch.created_at,
            **batch.snapshot}

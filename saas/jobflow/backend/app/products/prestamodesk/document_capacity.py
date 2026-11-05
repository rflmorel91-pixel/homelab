"""Bound private-document growth; retain the tenant lock until commit/rollback."""
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.platform.resource_limits import lock_tenant_capacity
from app.products.prestamodesk.models import ApplicationReviewDocument
from app.products.prestamodesk.private_documents import MAX_PRIVATE_DOCUMENT_BYTES


@dataclass(frozen=True)
class DocumentStorageLimits:
    tenant_bytes: int = 256 * 1024 * 1024
    tenant_documents: int = 1000
    application_documents: int = 20
    document_versions: int = 5


DOCUMENT_LIMITS = DocumentStorageLimits()


def require_document_capacity(
    db: Session, tenant_id: int, application_id: int,
    document_type: str, byte_size: int,
) -> None:
    if not 0 < byte_size <= MAX_PRIVATE_DOCUMENT_BYTES:
        raise HTTPException(413, "Document exceeds the 8 MiB limit")
    # All uploads, including different applications, serialize on this row.
    # Normal PostgreSQL READ COMMITTED sees the preceding uploader's commit.
    lock_tenant_capacity(db, tenant_id)
    document = ApplicationReviewDocument
    count, used_bytes, application_count, version_count = db.execute(
        select(
            func.count(document.id),
            func.coalesce(func.sum(document.byte_size), 0),
            func.count(document.id).filter(document.application_id == application_id),
            func.count(document.id).filter(
                document.application_id == application_id,
                document.document_type == document_type,
            ),
        ).where(document.tenant_id == tenant_id)
    ).one()
    limits = DOCUMENT_LIMITS
    if used_bytes + byte_size > limits.tenant_bytes:
        raise HTTPException(413, "El almacenamiento de documentos de este negocio está lleno. Contacte a soporte.")
    if count >= limits.tenant_documents:
        raise HTTPException(409, "Este negocio alcanzó el límite de documentos. Contacte a soporte.")
    if application_count >= limits.application_documents:
        raise HTTPException(409, "Esta solicitud alcanzó el límite de documentos. Contacte a soporte.")
    if version_count >= limits.document_versions:
        raise HTTPException(409, "Este tipo de documento alcanzó el límite de versiones en esta solicitud. Contacte a soporte.")

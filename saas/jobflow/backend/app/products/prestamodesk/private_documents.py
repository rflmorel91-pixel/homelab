"""Private local storage helpers for the isolated PrestamoDesk pilot."""

import hashlib
import os
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException


MAX_PRIVATE_DOCUMENT_BYTES = 8 * 1024 * 1024
_ALLOWED = {
    "application/pdf": ("pdf", lambda data: data.startswith(b"%PDF-")),
    "image/jpeg": ("jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": ("png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
}


def detect_document(content_type: str, data: bytes) -> tuple[str, str]:
    spec = _ALLOWED.get(content_type.split(";", 1)[0].strip().lower())
    if spec is None or not data or not spec[1](data):
        raise HTTPException(status_code=415, detail="Only valid PDF, JPEG, and PNG documents are accepted")
    return spec[0], content_type.split(";", 1)[0].strip().lower()


def storage_root() -> Path:
    return Path(os.environ.get(
        "PRESTAMODESK_PRIVATE_STORAGE_PATH",
        "/var/lib/jobflow-private/prestamodesk",
    )).resolve()


def store_private_document(tenant_id: int, application_id: int, data: bytes, extension: str) -> tuple[UUID, str, str]:
    root = storage_root()
    tenant_directory = root / str(tenant_id)
    directory = tenant_directory / str(application_id)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    tenant_directory.mkdir(mode=0o700, exist_ok=True)
    directory.mkdir(mode=0o700, exist_ok=True)
    for private_directory in (root, tenant_directory, directory):
        os.chmod(private_directory, 0o700)
    storage_ref = uuid4()
    file_key = f"{tenant_id}/{application_id}/{storage_ref}.{extension}"
    target = (root / file_key).resolve()
    if not target.is_relative_to(root):
        raise RuntimeError("Resolved private document path escaped storage root")
    fd, temporary = tempfile.mkstemp(prefix=".upload-", dir=directory)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        Path(temporary).unlink(missing_ok=True)
        raise
    return storage_ref, file_key, hashlib.sha256(data).hexdigest()


def private_document_path(file_key: str) -> Path:
    root = storage_root()
    target = (root / file_key).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise FileNotFoundError
    return target


def remove_private_document(file_key: str) -> None:
    try:
        private_document_path(file_key).unlink(missing_ok=True)
    except (FileNotFoundError, OSError):
        pass

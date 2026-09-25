from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DocumentType = Literal["cedula", "passport", "other"]
BorrowerStatus = Literal["active", "inactive"]


class BorrowerBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    document_type: DocumentType = "cedula"
    document_number: str | None = Field(
        default=None,
        max_length=50,
    )
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = None
    municipality: str | None = Field(
        default=None,
        max_length=120,
    )
    province: str | None = Field(
        default=None,
        max_length=120,
    )
    status: BorrowerStatus = "active"
    notes: str | None = None


class BorrowerCreate(BorrowerBase):
    model_config = ConfigDict(extra="forbid")


class BorrowerUpdate(BorrowerBase):
    model_config = ConfigDict(extra="forbid")


class BorrowerRead(BorrowerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


InvoiceStatus = Literal[
    "draft",
    "sent",
    "paid",
]


class InvoiceBase(BaseModel):
    job_id: int
    description: str | None = None
    amount: Decimal
    status: InvoiceStatus = "draft"


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(InvoiceBase):
    pass


class InvoiceRead(InvoiceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

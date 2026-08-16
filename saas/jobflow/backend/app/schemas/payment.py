from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


PaymentMethod = Literal[
    "cash",
    "check",
    "card",
    "bank_transfer",
    "other",
]


class PaymentBase(BaseModel):
    invoice_id: int
    amount: Decimal
    method: PaymentMethod
    reference: str | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

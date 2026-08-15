from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


EstimateStatus = Literal[
    "draft",
    "sent",
    "approved",
    "declined",
]


class EstimateBase(BaseModel):
    job_id: int
    description: str | None = None
    amount: Decimal
    status: EstimateStatus = "draft"


class EstimateCreate(EstimateBase):
    pass


class EstimateUpdate(EstimateBase):
    pass


class EstimateRead(EstimateBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

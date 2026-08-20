from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


RenewalStatus = Literal[
    "active",
    "renewal_in_progress",
    "renewed",
    "archived",
]


class RenewalItemBase(BaseModel):
    name: str
    category: str = "other"
    renewal_date: date
    status: RenewalStatus = "active"
    owner_name: str | None = None
    reminder_days: int = Field(
        default=30,
        ge=0,
        le=3650,
    )
    notes: str | None = None


class RenewalItemCreate(RenewalItemBase):
    model_config = ConfigDict(
        extra="forbid",
    )


class RenewalItemUpdate(RenewalItemBase):
    model_config = ConfigDict(
        extra="forbid",
    )


class RenewalItemRead(RenewalItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

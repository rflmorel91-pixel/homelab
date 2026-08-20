from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class RenewalItemBase(BaseModel):
    name: str
    renewal_date: date


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

    model_config = ConfigDict(
        from_attributes=True,
    )

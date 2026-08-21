from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
)


RenewalStatus = Literal[
    "active",
    "renewal_in_progress",
    "renewed",
    "archived",
    "inactive",
]

RenewalState = Literal[
    "upcoming",
    "due_soon",
    "expired",
    "inactive",
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

    @computed_field
    @property
    def days_until_renewal(self) -> int:
        return (
            self.renewal_date
            - date.today()
        ).days

    @computed_field
    @property
    def renewal_state(self) -> RenewalState:
        days = self.days_until_renewal

        if self.status in {
            "inactive",
            "archived",
        }:
            return "inactive"

        if days < 0:
            return "expired"

        if days <= self.reminder_days:
            return "due_soon"

        return "upcoming"


class RenewalDashboard(BaseModel):
    total: int
    expired: int
    due_soon: int
    upcoming: int
    inactive: int
    items: list[RenewalItemRead]


class RenewalReminderDeliveryRead(BaseModel):
    id: int
    renewal_item_id: int
    channel: str
    status: str
    scheduled_for: datetime
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

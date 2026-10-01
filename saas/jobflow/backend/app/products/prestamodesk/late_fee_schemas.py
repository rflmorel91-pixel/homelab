from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class LateFeePolicyUpdate(BaseModel):
    enabled: bool = False
    daily_rate_percent: Decimal = Field(
        ge=0,
        le=100,
        max_digits=7,
        decimal_places=4,
    )
    grace_days: int = Field(ge=0, le=365)
    cap_percent: Decimal = Field(
        ge=0,
        le=1000,
        max_digits=7,
        decimal_places=4,
    )
    effective_date: date

    @model_validator(mode="after")
    def validate_enabled_policy(self):
        if self.enabled and self.daily_rate_percent <= 0:
            raise ValueError(
                "Enabled policy requires a positive daily rate"
            )

        if self.enabled and self.cap_percent <= 0:
            raise ValueError(
                "Enabled policy requires a positive cap"
            )

        return self

    model_config = ConfigDict(extra="forbid")


class LateFeePolicyRead(LateFeePolicyUpdate):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
)


RequiredText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]


class PublicLeadCreate(BaseModel):
    business_name: RequiredText
    contact_name: RequiredText
    email: RequiredText
    phone: str | None = None
    service_type: RequiredText
    message: str | None = None

    model_config = ConfigDict(extra="forbid")


class PublicLeadRead(BaseModel):
    lead_id: int
    status: str


class LeadRead(BaseModel):
    id: int
    business_name: str
    contact_name: str
    email: str
    phone: str | None
    service_type: str
    message: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

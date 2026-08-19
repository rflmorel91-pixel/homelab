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


class LeadUpdate(BaseModel):
    status: str

    model_config = ConfigDict(extra="forbid")


class LeadRead(BaseModel):
    id: int
    business_name: str
    contact_name: str
    email: str
    phone: str | None
    service_type: str
    message: str | None
    status: str
    converted_tenant_id: int | None = None
    converted_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


TenantSlug = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    ),
]


class LeadProvisionRequest(BaseModel):
    owner_user_id: int
    tenant_slug: TenantSlug

    model_config = ConfigDict(extra="forbid")


class ProvisionedTenantRead(BaseModel):
    id: int
    name: str
    slug: str
    status: str


class ProvisionedOwnerRead(BaseModel):
    user_id: int
    email: str
    display_name: str
    role: str


class LeadProvisionRead(BaseModel):
    lead_id: int
    status: str
    converted_at: datetime
    tenant: ProvisionedTenantRead
    owner: ProvisionedOwnerRead


class ProvisioningOwnerRead(BaseModel):
    user_id: int
    email: str
    display_name: str


class LeadProvisioningOptionsRead(BaseModel):
    owners: list[ProvisioningOwnerRead]

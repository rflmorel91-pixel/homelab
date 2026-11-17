from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PropertyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    address: str = Field(min_length=1, max_length=300)
    property_type: Literal["residential", "multifamily", "commercial"] = "residential"
    total_units: int = Field(default=1, ge=1, le=10000)
    model_config = ConfigDict(extra="forbid")


class PropertyRead(PropertyCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PropertyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    address: str | None = Field(default=None, min_length=1, max_length=300)
    property_type: Literal["residential", "multifamily", "commercial"] | None = None
    total_units: int | None = Field(default=None, ge=1, le=10000)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def reject_null_fields(self):
        for name in ("name", "address", "property_type", "total_units"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ResidentCreate(BaseModel):
    property_id: int
    name: str = Field(min_length=1, max_length=160)
    unit: str = Field(min_length=1, max_length=60)
    email: str | None = Field(default=None, max_length=320)
    model_config = ConfigDict(extra="forbid")


class ResidentRead(ResidentCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    trade: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=60)
    email: str | None = Field(default=None, max_length=320)
    insurance_expires: date | None = None
    model_config = ConfigDict(extra="forbid")


class VendorRead(VendorCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VendorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    trade: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=60)
    email: str | None = Field(default=None, max_length=320)
    insurance_expires: date | None = None
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def validate_update(self):
        for name in ("name", "trade"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        for name in ("phone", "email"):
            if name in self.model_fields_set and getattr(self, name) == "":
                setattr(self, name, None)
        return self


class WorkOrderCreate(BaseModel):
    property_id: int
    resident_id: int | None = None
    vendor_id: int | None = None
    title: str = Field(min_length=1, max_length=180)
    unit: str = Field(default="", max_length=80)
    description: str | None = Field(default=None, max_length=5000)
    priority: Literal["low", "normal", "high", "emergency"] = "normal"
    target_date: date | None = None
    model_config = ConfigDict(extra="forbid")


class WorkOrderUpdate(BaseModel):
    resident_id: int | None = None
    vendor_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=180)
    unit: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=5000)
    priority: Literal["low", "normal", "high", "emergency"] | None = None
    status: Literal["open", "scheduled", "in_progress", "waiting", "completed", "cancelled"] | None = None
    target_date: date | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for name in ("title", "unit", "priority", "status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class WorkOrderRead(WorkOrderCreate):
    id: int
    status: str
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

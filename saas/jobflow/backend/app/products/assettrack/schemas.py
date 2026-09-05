from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AssetStatus = Literal[
    "active",
    "inactive",
    "retired",
    "lost",
]


class AssetBase(BaseModel):
    external_id: str | None = Field(
        default=None,
        max_length=100,
    )
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    asset_type: str = Field(
        default="other",
        min_length=1,
        max_length=50,
    )
    manufacturer: str | None = Field(
        default=None,
        max_length=200,
    )
    model: str | None = Field(
        default=None,
        max_length=200,
    )
    serial_number: str | None = Field(
        default=None,
        max_length=200,
    )
    status: AssetStatus = "active"
    attributes: dict[str, Any] = Field(
        default_factory=dict,
    )


class AssetCreate(AssetBase):
    model_config = ConfigDict(
        extra="forbid",
    )


class AssetUpdate(AssetBase):
    model_config = ConfigDict(
        extra="forbid",
    )


class AssetRead(AssetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class AssetServiceEventBase(BaseModel):
    event_type: str = Field(
        min_length=1,
        max_length=50,
    )
    occurred_at: datetime
    summary: str = Field(
        min_length=1,
        max_length=500,
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
    )


class AssetServiceEventCreate(
    AssetServiceEventBase
):
    model_config = ConfigDict(
        extra="forbid",
    )


class AssetServiceEventRead(
    AssetServiceEventBase
):
    id: int
    asset_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

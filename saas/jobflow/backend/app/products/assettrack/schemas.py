from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    name: str


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

    model_config = ConfigDict(
        from_attributes=True,
    )

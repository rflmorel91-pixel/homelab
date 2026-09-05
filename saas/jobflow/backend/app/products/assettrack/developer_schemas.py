from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class DeveloperApiKeyCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("API key name is required")

        return normalized

    model_config = ConfigDict(
        extra="forbid",
    )


class DeveloperApiKeyRead(BaseModel):
    id: int
    name: str
    key_prefix: str
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class DeveloperApiKeyCreated(DeveloperApiKeyRead):
    api_key: str


class DeveloperStatusRead(BaseModel):
    product: str
    api_version: str
    status: str

from pydantic import BaseModel, ConfigDict


class PublicRequestCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    project_title: str
    project_description: str | None = None

    model_config = ConfigDict(extra="forbid")


class PublicRequestRead(BaseModel):
    request_id: int
    status: str

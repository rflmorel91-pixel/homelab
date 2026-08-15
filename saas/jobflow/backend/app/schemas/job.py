from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobBase(BaseModel):
    customer_id: int
    title: str
    description: str | None = None
    status: str = "customer_requested"


class JobCreate(JobBase):
    pass


class JobUpdate(JobBase):
    pass


class JobRead(JobBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

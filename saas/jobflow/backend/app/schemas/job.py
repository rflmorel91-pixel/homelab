from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


JobStatus = Literal[
    "customer_requested",
    "quoted",
    "approved",
    "scheduled",
    "in_progress",
    "completed",
    "invoiced",
    "paid",
]


class JobBase(BaseModel):
    customer_id: int
    title: str
    description: str | None = None
    status: JobStatus = "customer_requested"


class JobCreate(JobBase):
    pass


class JobUpdate(JobBase):
    pass


class JobRead(JobBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

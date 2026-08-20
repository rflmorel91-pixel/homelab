from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class ScheduleBase(BaseModel):
    job_id: int
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_schedule_times(self):
        if (
            self.scheduled_end is not None
            and self.scheduled_end < self.scheduled_start
        ):
            raise ValueError(
                "scheduled_end must be after scheduled_start"
            )

        return self


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(ScheduleBase):
    pass


class ScheduleRead(ScheduleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

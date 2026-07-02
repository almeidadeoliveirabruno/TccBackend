from pydantic import BaseModel, field_validator
from datetime import time


class ScheduleItem(BaseModel):
    day_of_week: int
    time_begin: time
    time_end: time

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v):
        if v < 0 or v > 6:
            raise ValueError("day_of_week must be between 0 (Sunday) and 6 (Saturday)")
        return v

    @field_validator("time_end")
    @classmethod
    def validate_time_end(cls, v, info):
        time_begin = info.data.get("time_begin")
        if time_begin and v <= time_begin:
            raise ValueError("time_end must be greater than time_begin")
        return v


class AvailabilityCreate(BaseModel):
    availability: list[ScheduleItem]


class ScheduleUpdate(BaseModel):
    day_of_week: int
    time_begin: time
    time_end: time

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v):
        if v < 0 or v > 6:
            raise ValueError("day_of_week must be between 0 (Sunday) and 6 (Saturday)")
        return v

    @field_validator("time_end")
    @classmethod
    def validate_time_end(cls, v, info):
        time_begin = info.data.get("time_begin")
        if time_begin and v <= time_begin:
            raise ValueError("time_end must be greater than time_begin")
        return v


class ScheduleCreatedResponse(BaseModel):
    id: int
    day_of_week: int
    time_begin: time
    time_end: time

    class Config:
        from_attributes = True


class AvailabilityResponse(BaseModel):
    dentist_id: int
    schedules_created: list[ScheduleCreatedResponse]
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    test_id: int
    centre_id: int
    appointment_time: datetime

    @field_validator("appointment_time")
    @classmethod
    def appointment_must_be_future(cls, v: datetime) -> datetime:
        # Compare in a timezone-safe way; reject naive-vs-aware mismatches gracefully.
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        if v <= now:
            raise ValueError("appointment_time must be in the future.")
        return v


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    test_id: int
    centre_id: int
    appointment_time: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: int


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    amount: Decimal
    status: PaymentStatus
    provider_reference: str
    created_at: datetime

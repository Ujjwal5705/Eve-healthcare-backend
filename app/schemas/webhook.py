from pydantic import BaseModel, Field

from app.models.payment import PaymentStatus


class PaymentWebhookPayload(BaseModel):
    event_id: str = Field(..., min_length=1)
    provider_reference: str = Field(..., min_length=1)
    status: PaymentStatus

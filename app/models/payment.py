import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SAEnum(PaymentStatus, name="payment_status"), nullable=False)

    # The ID the *simulated payment provider* assigns to this transaction.
    # Used by the webhook to find the right payment idempotently.
    provider_reference = Column(String, unique=True, index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("Booking", back_populates="payments")

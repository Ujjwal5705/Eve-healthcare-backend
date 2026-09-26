import enum

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Numeric,
    DateTime,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("diagnostic_tests.id"), nullable=False)
    centre_id = Column(Integer, ForeignKey("diagnostic_centres.id"), nullable=False)

    appointment_time = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        SAEnum(BookingStatus, name="booking_status"),
        nullable=False,
        default=BookingStatus.PENDING,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="bookings")
    test = relationship("DiagnosticTest", back_populates="bookings")
    centre = relationship("DiagnosticCentre", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking")

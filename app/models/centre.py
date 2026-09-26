from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tests = relationship(
        "DiagnosticTest", back_populates="centre", cascade="all, delete-orphan"
    )
    bookings = relationship("Booking", back_populates="centre")


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    centre_id = Column(
        Integer, ForeignKey("diagnostic_centres.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    centre = relationship("DiagnosticCentre", back_populates="tests")
    bookings = relationship("Booking", back_populates="test")

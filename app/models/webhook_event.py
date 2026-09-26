from sqlalchemy import Column, Integer, String, DateTime, func

from app.database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    payload = Column(String, nullable=True)  # raw JSON string, for audit/debug
    received_at = Column(DateTime(timezone=True), server_default=func.now())

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.booking import Booking, BookingStatus
from app.models.webhook_event import WebhookEvent
from app.schemas.webhook import PaymentWebhookPayload

router = APIRouter(prefix="/payments", tags=["Webhooks"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
def payment_webhook(payload: PaymentWebhookPayload, db: Session = Depends(get_db)):
    # Step 1: Check if we've already processed this exact event.
    existing_event = (
        db.query(WebhookEvent).filter(WebhookEvent.event_id == payload.event_id).first()
    )
    if existing_event:
        # Duplicate delivery — acknowledge as success, do nothing further.
        return {
            "status": "ok",
            "detail": "Event already processed (duplicate ignored).",
        }

    # Step 2: Find the payment this event refers to.
    payment = (
        db.query(Payment)
        .filter(Payment.provider_reference == payload.provider_reference)
        .first()
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payment found for the given provider_reference.",
        )

    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if not booking:
        # Should not normally happen (FK integrity), but guard anyway.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated booking not found.",
        )

    # Step 3: Apply the update.
    payment.status = payload.status
    booking.status = (
        BookingStatus.CONFIRMED
        if payload.status == PaymentStatus.SUCCESS
        else BookingStatus.FAILED
    )

    # Step 4: Record that we've now processed this event_id, in the SAME transaction.
    webhook_event = WebhookEvent(
        event_id=payload.event_id, payload=json.dumps(payload.model_dump(mode="json"))
    )
    db.add(webhook_event)

    try:
        db.commit()
    except IntegrityError:
        # Race condition guard: two identical webhook requests arrived at the exact same time
        # and both passed the "existing_event" check above before either committed.
        # The unique constraint on event_id will reject the second commit — treat it as a duplicate.
        db.rollback()
        return {
            "status": "ok",
            "detail": "Event already processed (duplicate ignored).",
        }

    db.refresh(payment)
    return {
        "status": "ok",
        "payment_status": payment.status.value,
        "booking_status": booking.status.value,
    }

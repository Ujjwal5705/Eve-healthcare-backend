from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services import payment_simulator

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def make_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == payment_in.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found."
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pay for this booking.",
        )

    if booking.status not in (BookingStatus.PENDING, BookingStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process payment for a booking with status {booking.status.value}.",
        )

    result = payment_simulator.simulate_payment_result()

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=result,
        provider_reference=payment_simulator.generate_provider_reference(),
    )
    db.add(payment)

    booking.status = (
        BookingStatus.CONFIRMED
        if result == PaymentStatus.SUCCESS
        else BookingStatus.FAILED
    )

    db.commit()
    db.refresh(payment)
    return payment

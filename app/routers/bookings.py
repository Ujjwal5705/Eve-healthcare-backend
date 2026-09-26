from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreate, BookingOut

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = (
        db.query(DiagnosticTest).filter(DiagnosticTest.id == booking_in.test_id).first()
    )
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic test not found."
        )

    centre = (
        db.query(DiagnosticCentre)
        .filter(DiagnosticCentre.id == booking_in.centre_id)
        .first()
    )
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic centre not found."
        )

    # Make sure the test actually belongs to the centre the user selected.
    if test.centre_id != centre.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This test is not offered at the selected centre.",
        )

    # Prevent the same user from double-booking the same test/centre/time slot.
    duplicate = (
        db.query(Booking)
        .filter(
            Booking.user_id == current_user.id,
            Booking.test_id == test.id,
            Booking.centre_id == centre.id,
            Booking.appointment_time == booking_in.appointment_time,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active booking for this test at this centre and time.",
        )

    booking = Booking(
        user_id=current_user.id,
        test_id=test.id,
        centre_id=centre.id,
        appointment_time=booking_in.appointment_time,
        amount=test.price,  # snapshot the price at booking time
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("", response_model=List[BookingOut])
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Booking).filter(Booking.user_id == current_user.id).all()


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found."
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking.",
        )

    return booking


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found."
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this booking.",
        )

    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking with status {booking.status.value}.",
        )

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking

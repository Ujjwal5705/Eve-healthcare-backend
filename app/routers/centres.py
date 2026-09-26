from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.schemas.centre import (
    CentreCreate,
    CentreOut,
    CentreOutBrief,
    TestCreate,
    TestOut,
)

router = APIRouter(prefix="/centres", tags=["Diagnostic Centres & Tests"])


@router.post("", response_model=CentreOut, status_code=status.HTTP_201_CREATED)
def create_centre(
    centre_in: CentreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre = DiagnosticCentre(name=centre_in.name, location=centre_in.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.get("", response_model=List[CentreOutBrief])
def list_centres(
    location: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(DiagnosticCentre)
    if location:
        query = query.filter(DiagnosticCentre.location.ilike(f"%{location}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{centre_id}", response_model=CentreOut)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = (
        db.query(DiagnosticCentre)
        .options(joinedload(DiagnosticCentre.tests))
        .filter(DiagnosticCentre.id == centre_id)
        .first()
    )
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic centre not found."
        )
    return centre


@router.post(
    "/{centre_id}/tests", response_model=TestOut, status_code=status.HTTP_201_CREATED
)
def add_test_to_centre(
    centre_id: int,
    test_in: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic centre not found."
        )

    test = DiagnosticTest(name=test_in.name, price=test_in.price, centre_id=centre.id)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("/{centre_id}/tests", response_model=List[TestOut])
def list_tests_for_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic centre not found."
        )

    return db.query(DiagnosticTest).filter(DiagnosticTest.centre_id == centre_id).all()

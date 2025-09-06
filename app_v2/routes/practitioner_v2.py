from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app_v2.database import get_db
from app_v2.models.practitioner import PractitionerV2
from app_v2.schemas.practitioner import PractitionerCreate, PractitionerRead, PractitionerUpdate

router = APIRouter(prefix="/practitioners", tags=["practitioners v2"])


@router.get("/", response_model=List[PractitionerRead])
def list_practitioners(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    name: Optional[str] = None,
    organization_id: Optional[int] = None,
    specialty_code: Optional[str] = None,
    gender: Optional[str] = None,
    identifier: Optional[str] = None,
):
    """
    List practitioners with filtering options.
    
    - **name**: Filter by practitioner name (partial match)
    - **organization_id**: Filter by organization (practitioners at specific hospital/clinic)
    - **specialty_code**: Filter by medical specialty (cardiology, neurology, etc.)
    - **gender**: Filter by gender
    - **identifier**: Filter by practitioner identifier
    """
    query = db.query(PractitionerV2)
    
    if name is not None:
        query = query.filter(PractitionerV2.name.ilike(f"%{name}%"))
    if organization_id is not None:
        query = query.filter(PractitionerV2.organization_id == organization_id)
    if specialty_code is not None:
        query = query.filter(PractitionerV2.specialty_code == specialty_code)
    if gender is not None:
        query = query.filter(PractitionerV2.gender == gender)
    if identifier is not None:
        query = query.filter(PractitionerV2.identifier == identifier)

    practitioners = query.order_by(PractitionerV2.name.asc()).limit(limit).offset(offset).all()
    return practitioners


@router.get("/{practitioner_id}", response_model=PractitionerRead)
def get_practitioner(practitioner_id: int, db: Session = Depends(get_db)):
    """Get a specific practitioner by ID."""
    practitioner = db.query(PractitionerV2).get(practitioner_id)
    if not practitioner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practitioner not found")
    return practitioner


@router.post("/", response_model=PractitionerRead, status_code=status.HTTP_201_CREATED)
def create_practitioner(payload: PractitionerCreate, db: Session = Depends(get_db)):
    """Create a new practitioner."""
    new_practitioner = PractitionerV2(**payload.model_dump(exclude_unset=True))
    db.add(new_practitioner)
    db.commit()
    db.refresh(new_practitioner)
    return new_practitioner


@router.put("/{practitioner_id}", response_model=PractitionerRead)
def update_practitioner(practitioner_id: int, payload: PractitionerUpdate, db: Session = Depends(get_db)):
    """Update an existing practitioner."""
    practitioner = db.query(PractitionerV2).get(practitioner_id)
    if not practitioner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practitioner not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(practitioner, key, value)

    db.commit()
    db.refresh(practitioner)
    return practitioner


@router.delete("/{practitioner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_practitioner(practitioner_id: int, db: Session = Depends(get_db)):
    """Delete a practitioner."""
    practitioner = db.query(PractitionerV2).get(practitioner_id)
    if not practitioner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practitioner not found")

    db.delete(practitioner)
    db.commit()
    return None

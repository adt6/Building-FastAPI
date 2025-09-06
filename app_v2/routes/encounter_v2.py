from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app_v2.database import get_db
from app_v2.models.encounter import EncounterV2
from app_v2.schemas.encounter import EncounterCreate, EncounterRead, EncounterUpdate

router = APIRouter(prefix="/encounters", tags=["encounters v2"])


@router.get("/", response_model=List[EncounterRead])
def list_encounters(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    patient_id: Optional[int] = None,
    practitioner_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    start_from: Optional[datetime] = None,
    start_to: Optional[datetime] = None,
    class_code: Optional[str] = None,
):
    """
    List encounters with filtering options.
    
    - **patient_id**: Filter by specific patient (patient-based encounters)
    - **practitioner_id**: Filter by specific practitioner
    - **organization_id**: Filter by specific organization
    - **status**: Filter by encounter status (scheduled, completed, cancelled, etc.)
    - **start_from**: Encounters starting from this date/time
    - **start_to**: Encounters starting before this date/time
    - **class_code**: Filter by encounter class (emergency, outpatient, etc.)
    """
    query = db.query(EncounterV2)
    
    if patient_id is not None:
        query = query.filter(EncounterV2.patient_id == patient_id)
    if practitioner_id is not None:
        query = query.filter(EncounterV2.practitioner_id == practitioner_id)
    if organization_id is not None:
        query = query.filter(EncounterV2.organization_id == organization_id)
    if status is not None:
        query = query.filter(EncounterV2.status == status)
    if start_from is not None:
        query = query.filter(EncounterV2.start_time >= start_from)
    if start_to is not None:
        query = query.filter(EncounterV2.start_time <= start_to)
    if class_code is not None:
        query = query.filter(EncounterV2.class_code == class_code)

    encounters = query.order_by(EncounterV2.start_time.desc()).limit(limit).offset(offset).all()
    return encounters


@router.get("/{encounter_id}", response_model=EncounterRead)
def get_encounter(encounter_id: int, db: Session = Depends(get_db)):
    """Get a specific encounter by ID."""
    encounter = db.query(EncounterV2).get(encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    return encounter


@router.post("/", response_model=EncounterRead, status_code=status.HTTP_201_CREATED)
def create_encounter(payload: EncounterCreate, db: Session = Depends(get_db)):
    """Create a new encounter."""
    new_encounter = EncounterV2(**payload.model_dump(exclude_unset=True))
    db.add(new_encounter)
    db.commit()
    db.refresh(new_encounter)
    return new_encounter


@router.put("/{encounter_id}", response_model=EncounterRead)
def update_encounter(encounter_id: int, payload: EncounterUpdate, db: Session = Depends(get_db)):
    """Update an existing encounter."""
    encounter = db.query(EncounterV2).get(encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(encounter, key, value)

    db.commit()
    db.refresh(encounter)
    return encounter


@router.delete("/{encounter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_encounter(encounter_id: int, db: Session = Depends(get_db)):
    """Delete an encounter."""
    encounter = db.query(EncounterV2).get(encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    db.delete(encounter)
    db.commit()
    return None

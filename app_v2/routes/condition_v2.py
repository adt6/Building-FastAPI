from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app_v2.database import get_db
from app_v2.models.condition import ConditionV2
from app_v2.schemas.condition import ConditionCreate, ConditionRead, ConditionUpdate

router = APIRouter(prefix="/conditions", tags=["conditions v2"])


@router.get("/", response_model=List[ConditionRead])
def list_conditions(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    patient_id: Optional[int] = None,
    encounter_id: Optional[int] = None,
    code: Optional[str] = None,
    clinical_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    category_code: Optional[str] = None,
    onset_from: Optional[datetime] = None,
    onset_to: Optional[datetime] = None,
):
    """
    List conditions with filtering options.
    
    - **patient_id**: Filter by specific patient (patient-based conditions)
    - **encounter_id**: Filter by specific encounter
    - **code**: Filter by condition code (e.g., diabetes, hypertension)
    - **clinical_status**: Filter by clinical status (active, inactive, resolved)
    - **verification_status**: Filter by verification status (confirmed, provisional, differential)
    - **category_code**: Filter by condition category
    - **onset_from**: Conditions with onset after this date/time
    - **onset_to**: Conditions with onset before this date/time
    """
    query = db.query(ConditionV2)
    
    if patient_id is not None:
        query = query.filter(ConditionV2.patient_id == patient_id)
    if encounter_id is not None:
        query = query.filter(ConditionV2.encounter_id == encounter_id)
    if code is not None:
        query = query.filter(ConditionV2.code.ilike(f"%{code}%"))
    if clinical_status is not None:
        query = query.filter(ConditionV2.clinical_status == clinical_status)
    if verification_status is not None:
        query = query.filter(ConditionV2.verification_status == verification_status)
    if category_code is not None:
        query = query.filter(ConditionV2.category_code == category_code)
    if onset_from is not None:
        query = query.filter(ConditionV2.onset_time >= onset_from)
    if onset_to is not None:
        query = query.filter(ConditionV2.onset_time <= onset_to)

    conditions = query.order_by(ConditionV2.recorded_date.desc()).limit(limit).offset(offset).all()
    return conditions


@router.get("/{condition_id}", response_model=ConditionRead)
def get_condition(condition_id: int, db: Session = Depends(get_db)):
    """Get a specific condition by ID."""
    condition = db.query(ConditionV2).get(condition_id)
    if not condition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")
    return condition


@router.post("/", response_model=ConditionRead, status_code=status.HTTP_201_CREATED)
def create_condition(payload: ConditionCreate, db: Session = Depends(get_db)):
    """Create a new condition."""
    new_condition = ConditionV2(**payload.model_dump(exclude_unset=True))
    db.add(new_condition)
    db.commit()
    db.refresh(new_condition)
    return new_condition


@router.put("/{condition_id}", response_model=ConditionRead)
def update_condition(condition_id: int, payload: ConditionUpdate, db: Session = Depends(get_db)):
    """Update an existing condition."""
    condition = db.query(ConditionV2).get(condition_id)
    if not condition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(condition, key, value)

    db.commit()
    db.refresh(condition)
    return condition


@router.delete("/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condition(condition_id: int, db: Session = Depends(get_db)):
    """Delete a condition."""
    condition = db.query(ConditionV2).get(condition_id)
    if not condition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")

    db.delete(condition)
    db.commit()
    return None

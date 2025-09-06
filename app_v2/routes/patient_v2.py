from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app_v2.database import get_db
from app_v2.models.patient import PatientV2
from app_v2.schemas.patient import PatientCreate, PatientRead, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients v2"]) 


@router.get("/", response_model=List[PatientRead])
def list_patients(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    identifier: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    active: Optional[bool] = None,
):
    query = db.query(PatientV2)
    if identifier is not None:
        query = query.filter(PatientV2.identifier == identifier)
    if first_name is not None:
        query = query.filter(PatientV2.first_name.ilike(f"%{first_name}%"))
    if last_name is not None:
        query = query.filter(PatientV2.last_name.ilike(f"%{last_name}%"))
    if active is not None:
        query = query.filter(PatientV2.active == active)

    patients = query.order_by(PatientV2.id.asc()).limit(limit).offset(offset).all()
    return patients


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(PatientV2).get(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.post("/", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    new_patient = PatientV2(**payload.model_dump(exclude_unset=True))
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(PatientV2).get(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(PatientV2).get(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    db.delete(patient)
    db.commit()
    return None

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Practitioner
from app.schemas.practitioner import PractitionerCreate, PractitionerResponse
from typing import List

router = APIRouter(prefix="/practitioners", tags=["practitioners"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a new practitioner
@router.post("/", response_model=PractitionerResponse)
def create_practitioner(practitioner: PractitionerCreate, db: Session = Depends(get_db)):
    new_practitioner = Practitioner(**practitioner.model_dump())
    db.add(new_practitioner)
    db.commit()
    db.refresh(new_practitioner)
    return new_practitioner

# Get all practitioners
@router.get("/", response_model=List[PractitionerResponse])
def get_all_practitioners(db: Session = Depends(get_db)):
    return db.query(Practitioner).all()

# Get a practitioner by ID
@router.get("/{practitioner_id}", response_model=PractitionerResponse)
def get_practitioner(practitioner_id: int, db: Session = Depends(get_db)):
    practitioner = db.query(Practitioner).filter(Practitioner.id == practitioner_id).first()
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return practitioner

# Update a practitioner by ID
@router.put("/{practitioner_id}", response_model=PractitionerResponse)
def update_practitioner(practitioner_id: int, updated_data: PractitionerCreate, db: Session = Depends(get_db)):
    practitioner = db.query(Practitioner).filter(Practitioner.id == practitioner_id).first()
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(practitioner, key, value)
    db.commit()
    db.refresh(practitioner)
    return practitioner

# Delete a practitioner by ID
@router.delete("/{practitioner_id}")
def delete_practitioner(practitioner_id: int, db: Session = Depends(get_db)):
    practitioner = db.query(Practitioner).filter(Practitioner.id == practitioner_id).first()
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    db.delete(practitioner)
    db.commit()
    return {"detail": "Practitioner deleted successfully"}

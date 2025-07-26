from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Encounter
from app.schemas.encounter import EncounterCreate, EncounterResponse
from typing import List

router = APIRouter(prefix="/encounters", tags=["encounters"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=EncounterResponse)
def create_encounter(encounter: EncounterCreate, db: Session = Depends(get_db)):
    new_encounter = Encounter(**encounter.model_dump())
    db.add(new_encounter)
    db.commit()
    db.refresh(new_encounter)
    return new_encounter

@router.get("/", response_model=List[EncounterResponse])
def get_all_encounters(db: Session = Depends(get_db)):
    return db.query(Encounter).all()

@router.get("/{encounter_id}", response_model=EncounterResponse)
def get_encounter(encounter_id: int, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter

@router.put("/{encounter_id}", response_model=EncounterResponse)
def update_encounter(encounter_id: int, updated_data: EncounterCreate, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(encounter, key, value)
    db.commit()
    db.refresh(encounter)
    return encounter

@router.delete("/{encounter_id}")
def delete_encounter(encounter_id: int, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    db.delete(encounter)
    db.commit()
    return {"detail": "Encounter deleted successfully"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Condition
from app.schemas.condition import ConditionCreate, ConditionResponse
from typing import List

router = APIRouter(prefix="/conditions", tags=["conditions"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ConditionResponse)
def create_condition(condition: ConditionCreate, db: Session = Depends(get_db)):
    new_condition = Condition(**condition.model_dump())
    db.add(new_condition)
    db.commit()
    db.refresh(new_condition)
    return new_condition

@router.get("/", response_model=List[ConditionResponse])
def get_all_conditions(db: Session = Depends(get_db)):
    return db.query(Condition).all()

@router.get("/{condition_id}", response_model=ConditionResponse)
def get_condition(condition_id: int, db: Session = Depends(get_db)):
    condition = db.query(Condition).filter(Condition.id == condition_id).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    return condition

@router.put("/{condition_id}", response_model=ConditionResponse)
def update_condition(condition_id: int, updated_data: ConditionCreate, db: Session = Depends(get_db)):
    condition = db.query(Condition).filter(Condition.id == condition_id).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(condition, key, value)
    db.commit()
    db.refresh(condition)
    return condition

@router.delete("/{condition_id}")
def delete_condition(condition_id: int, db: Session = Depends(get_db)):
    condition = db.query(Condition).filter(Condition.id == condition_id).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    db.delete(condition)
    db.commit()
    return {"detail": "Condition deleted successfully"}

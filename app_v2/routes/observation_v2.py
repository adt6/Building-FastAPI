from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app_v2.database import get_db
from app_v2.models.observation import ObservationV2
from app_v2.schemas.observation import ObservationResponse

router = APIRouter()

@router.get("/observations", response_model=List[ObservationResponse])
def get_observations(
    patient_id: Optional[int] = None,
    encounter_id: Optional[int] = None,
    practitioner_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get observations with optional filtering by patient, encounter, or practitioner."""
    query = db.query(ObservationV2)
    
    if patient_id:
        query = query.filter(ObservationV2.patient_id == patient_id)
    if encounter_id:
        query = query.filter(ObservationV2.encounter_id == encounter_id)
    if practitioner_id:
        query = query.filter(ObservationV2.practitioner_id == practitioner_id)
    
    observations = query.all()
    return observations

@router.get("/observations/{observation_id}", response_model=ObservationResponse)
def get_observation(observation_id: int, db: Session = Depends(get_db)):
    """Get a specific observation by ID."""
    observation = db.query(ObservationV2).filter(ObservationV2.id == observation_id).first()
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation

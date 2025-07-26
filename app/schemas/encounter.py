from pydantic import BaseModel
from datetime import date

class EncounterCreate(BaseModel):
    date: date
    patient_id: int
    practitioner_id: int

class EncounterResponse(EncounterCreate):
    id: int

    class Config:
        orm_mode = True

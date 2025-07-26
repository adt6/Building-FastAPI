from typing import Optional
from pydantic import BaseModel
from datetime import date

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    birth_date: date

class PatientResponse(PatientCreate):
    id: int

    class Config:
        orm_mode = True

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
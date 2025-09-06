from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class EncounterBase(BaseModel):
    identifier: Optional[str] = None
    patient_id: Optional[int] = None
    practitioner_id: Optional[int] = None
    organization_id: Optional[int] = None
    status: Optional[str] = None
    class_code: Optional[str] = None
    class_display: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reason_code: Optional[str] = None
    reason_display: Optional[str] = None


class EncounterCreate(EncounterBase):
    patient_id: int
    status: str
    start_time: datetime


class EncounterUpdate(EncounterBase):
    pass


class EncounterRead(EncounterBase):
    id: int

    class Config:
        from_attributes = True
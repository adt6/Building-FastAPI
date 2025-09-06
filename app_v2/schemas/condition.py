from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ConditionBase(BaseModel):
    patient_id: Optional[int] = None
    encounter_id: Optional[int] = None
    code: Optional[str] = None
    system: Optional[str] = None
    display: Optional[str] = None
    category_code: Optional[str] = None
    clinical_status: Optional[str] = None
    verification_status: Optional[str] = None
    onset_time: Optional[datetime] = None
    abatement_time: Optional[datetime] = None
    recorded_date: Optional[datetime] = None


class ConditionCreate(ConditionBase):
    patient_id: int
    code: str


class ConditionUpdate(ConditionBase):
    pass


class ConditionRead(ConditionBase):
    id: int

    class Config:
        from_attributes = True

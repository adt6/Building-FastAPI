from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ObservationResponse(BaseModel):
    id: int
    patient_id: int
    encounter_id: Optional[int] = None
    practitioner_id: Optional[int] = None
    identifier: Optional[str] = None
    status: str
    code: str
    code_system: Optional[str] = None
    code_display: Optional[str] = None
    value_quantity: Optional[float] = None
    value_unit: Optional[str] = None
    value_string: Optional[str] = None
    effective_time: Optional[datetime] = None
    issued_time: Optional[datetime] = None

    class Config:
        from_attributes = True
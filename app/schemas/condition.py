from pydantic import BaseModel

class ConditionCreate(BaseModel):
    description: str
    patient_id: int

class ConditionResponse(ConditionCreate):
    id: int

    class Config:
        orm_mode = True

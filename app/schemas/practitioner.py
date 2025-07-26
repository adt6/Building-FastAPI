from pydantic import BaseModel

class PractitionerCreate(BaseModel):
    name: str
    specialty: str

class PractitionerResponse(PractitionerCreate):
    id: int

    class Config:
        orm_mode = True

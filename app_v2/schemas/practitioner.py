from typing import Optional
from pydantic import BaseModel


class PractitionerBase(BaseModel):
    identifier: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    specialty_code: Optional[str] = None
    specialty_display: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    organization_id: Optional[int] = None


class PractitionerCreate(PractitionerBase):
    name: str


class PractitionerUpdate(PractitionerBase):
    pass


class PractitionerRead(PractitionerBase):
    id: int

    class Config:
        from_attributes = True

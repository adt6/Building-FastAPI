from typing import Optional
from datetime import date
from pydantic import BaseModel


class PatientBase(BaseModel):
    identifier: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    marital_status: Optional[str] = None
    language: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    deceased_date: Optional[str] = None
    active: Optional[bool] = True
    managing_organization_identifier: Optional[str] = None


class PatientCreate(PatientBase):
    first_name: str
    last_name: str
    birth_date: date


class PatientUpdate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int

    class Config:
        from_attributes = True

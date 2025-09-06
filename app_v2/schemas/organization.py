from typing import Optional
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    identifier: Optional[str] = None
    name: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    part_of_identifier: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    name: str


class OrganizationUpdate(OrganizationBase):
    pass


class OrganizationRead(OrganizationBase):
    id: int

    class Config:
        from_attributes = True

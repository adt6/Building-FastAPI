from sqlalchemy import Column, Integer, String
from app_v2.database import Base

class OrganizationV2(Base):
    __tablename__ = "organizations_v2"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, index=True)
    name = Column(String, nullable=False)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address_line = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    part_of_identifier = Column(String, nullable=True)
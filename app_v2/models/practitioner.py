from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app_v2.database import Base

class PractitionerV2(Base):
    __tablename__ = "practitioners_v2"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, index=True)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    specialty_code = Column(String, nullable=True)
    specialty_display = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations_v2.id"), nullable=True)

    organization = relationship("OrganizationV2")
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app_v2.database import Base

class EncounterV2(Base):
    __tablename__ = "encounters_v2"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients_v2.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners_v2.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations_v2.id"), nullable=True)

    status = Column(String, nullable=True)
    class_code = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_system = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    reason_code = Column(String, nullable=True)
    priority_code = Column(String, nullable=True)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=True)
    length_minutes = Column(Integer, nullable=True)
    location_identifier = Column(String, nullable=True)

    patient = relationship("PatientV2")
    practitioner = relationship("PractitionerV2")
    organization = relationship("OrganizationV2")
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app_v2.database import Base

class EncounterV2(Base):
    __tablename__ = "encounters_v2"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients_v2.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners_v2.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations_v2.id"), nullable=True)
    
    identifier = Column(String, index=True)
    status = Column(String, nullable=False)
    class_code = Column(String, nullable=True)
    class_display = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    reason_code = Column(String, nullable=True)
    reason_display = Column(String, nullable=True)

    patient = relationship("PatientV2")
    practitioner = relationship("PractitionerV2")
    organization = relationship("OrganizationV2")

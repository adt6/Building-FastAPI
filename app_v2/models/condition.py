from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app_v2.database import Base

class ConditionV2(Base):
    __tablename__ = "conditions_v2"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients_v2.id"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters_v2.id"), nullable=True)

    code = Column(String, nullable=False)
    system = Column(String, nullable=True)
    display = Column(String, nullable=True)
    category_code = Column(String, nullable=True)
    clinical_status = Column(String, nullable=True)
    verification_status = Column(String, nullable=True)
    onset_time = Column(DateTime, nullable=True)
    abatement_time = Column(DateTime, nullable=True)
    recorded_date = Column(DateTime, nullable=True)

    patient = relationship("PatientV2")
    encounter = relationship("EncounterV2")
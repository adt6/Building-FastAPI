from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app_v2.database import Base

class ObservationV2(Base):
    __tablename__ = "observations_v2"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients_v2.id"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters_v2.id"), nullable=True)
    practitioner_id = Column(Integer, ForeignKey("practitioners_v2.id"), nullable=True)
    
    identifier = Column(String, index=True)
    status = Column(String, nullable=False)
    code = Column(String, nullable=False)
    code_system = Column(String, nullable=True)
    code_display = Column(String, nullable=True)
    value_quantity = Column(Float, nullable=True)
    value_unit = Column(String, nullable=True)
    value_string = Column(String, nullable=True)
    effective_time = Column(DateTime, nullable=True)
    issued_time = Column(DateTime, nullable=True)

    patient = relationship("PatientV2")
    encounter = relationship("EncounterV2")
    practitioner = relationship("PractitionerV2") 
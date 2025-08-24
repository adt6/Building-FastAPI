from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app_v2.database import Base

class ObservationV2(Base):
    __tablename__ = "observations_v2"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients_v2.id"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters_v2.id"), nullable=True)

    status = Column(String, nullable=True)
    category_code = Column(String, nullable=True)
    code = Column(String, nullable=False)
    system = Column(String, nullable=True)
    display = Column(String, nullable=True)
    value_num = Column(Numeric, nullable=True)
    unit = Column(String, nullable=True)
    value_text = Column(String, nullable=True)
    effective_time = Column(DateTime, nullable=True)

    patient = relationship("PatientV2")
    encounter = relationship("EncounterV2")
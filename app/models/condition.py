from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Condition(Base):
    __tablename__ = "conditions"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)

    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient")
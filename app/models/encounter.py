from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Encounter(Base):
    __tablename__ = "encounters"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)

    patient_id = Column(Integer, ForeignKey("patients.id"))
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"))

    # Relationships
    patient = relationship("Patient")
    practitioner = relationship("Practitioner")
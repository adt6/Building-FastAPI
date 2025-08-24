from sqlalchemy import Column, Integer, String, Date, Boolean
from app_v2.database import Base

class PatientV2(Base):
    __tablename__ = "patients_v2"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, index=True)  # MRN/UUID from FHIR
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address_line = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    language = Column(String, nullable=True)
    race = Column(String, nullable=True)
    ethnicity = Column(String, nullable=True)
    deceased_date = Column(String, nullable=True)  # ISO string; can change to DateTime
    active = Column(Boolean, default=True)
    managing_organization_identifier = Column(String, nullable=True)
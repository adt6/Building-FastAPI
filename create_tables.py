from app.database import Base, engine
from app.models import Patient, Practitioner, Encounter, Condition

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")

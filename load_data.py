import json
from datetime import date
from app.database import SessionLocal
from app.models import Patient, Practitioner, Encounter, Condition

# Create DB session
db = SessionLocal()

# 1. Load and insert patients
with open("mock_data/patients.json") as f:
    patients = json.load(f)
    for p in patients:
        p["birth_date"] = date.fromisoformat(p["birth_date"])
        patient = Patient(**p)
        db.add(patient)
db.commit()
print(f" Inserted {len(patients)} patients")

# 2. Load and insert practitioners
with open("mock_data/practitioners.json") as f:
    practitioners = json.load(f)
    for pr in practitioners:
        practitioner = Practitioner(**pr)
        db.add(practitioner)
db.commit()
print(f" Inserted {len(practitioners)} practitioners")

# 3. Load and insert encounters
with open("mock_data/encounters.json") as f:
    encounters = json.load(f)
    for e in encounters:
        encounter = Encounter(
            date=date.fromisoformat(e["date"]),
            patient_id=e["patient_id"],
            practitioner_id=e["practitioner_id"]
        )
        db.add(encounter)
db.commit()
print(f"✅ Inserted {len(encounters)} encounters")

# 4. Load and insert conditions
with open("mock_data/conditions.json") as f:
    conditions = json.load(f)
    for c in conditions:
        condition = Condition(
            description=c["description"],
            patient_id=c["patient_id"]
        )
        db.add(condition)
db.commit()
print(f" Inserted {len(conditions)} conditions")

# Close the session
db.close()
print("All data loaded into the database successfully.")

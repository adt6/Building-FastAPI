from fastapi import FastAPI
from app.routes import patient, practitioner, encounter, condition

app = FastAPI()

app.include_router(patient.router)
app.include_router(practitioner.router)
app.include_router(encounter.router)
app.include_router(condition.router)

@app.get("/")
def root():
    return {"message": "API is running"}
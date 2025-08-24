from fastapi import FastAPI
from app_v2.routes import patient_v2, practitioner_v2, encounter_v2, condition_v2

app = FastAPI(title="Healthcare API v2", version="2.0.0")

# v2-only routers
app.include_router(patient_v2.router, prefix="/api/v2")
app.include_router(practitioner_v2.router, prefix="/api/v2")
app.include_router(encounter_v2.router, prefix="/api/v2")
app.include_router(condition_v2.router, prefix="/api/v2")

@app.get("/api/v2/health")
def health():
    return {"status": "ok", "api": "v2"}

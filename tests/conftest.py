import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app_v2.main import app
from app_v2.database import Base, get_db
from app_v2.models.patient import PatientV2


# Create a single in-memory SQLite engine for the entire test session
engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Create all tables once
Base.metadata.create_all(bind=engine)


def seed_data() -> None:
    db = TestingSessionLocal()
    try:
        if db.query(PatientV2).count() == 0:
            patient = PatientV2(first_name="John", last_name="Doe", birth_date="1990-01-01")
            db.add(patient)
            db.commit()
    finally:
        db.close()


seed_data()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c



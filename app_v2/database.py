from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Use the same DB as in your docker-compose
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres_1:pass@localhost:5432/healthcare_db"
)

# Create engine and session
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

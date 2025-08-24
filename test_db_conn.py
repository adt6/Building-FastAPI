from sqlalchemy import create_engine, text
import os

# Same URL as in app_v2/database.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres_1:pass@localhost:5432/healthcare_db"
)

print("Using:", DATABASE_URL)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

try:
    with engine.connect() as conn:
        # Show version
        version = conn.execute(text("SELECT version();")).scalar()
        print("Connected to:", version)

        # List public tables
        tables = conn.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)).fetchall()
        print("Tables:", [t[0] for t in tables])

except Exception as e:
    print("❌ Connection failed:", e)

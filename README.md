# 🏥 FastAPI Healthcare API

A comprehensive, production-ready FastAPI project for managing healthcare data using PostgreSQL and Docker. Built with clean architecture, comprehensive data modeling, and RESTful CRUD endpoints following FHIR (Fast Healthcare Interoperability Resources) standards.

---

## 📦 Features

- 🚀 **FastAPI v2** with modular structure and versioned APIs
- 🧠 **SQLAlchemy ORM** with PostgreSQL for robust data persistence
- 📄 **Pydantic schemas** for request/response validation
- 🐳 **Docker + docker-compose** for isolated development
- 🔁 **CRUD endpoints** for core FHIR-style entities
- 🔧 **Swagger UI** for interactive API testing
- 📊 **Comprehensive data modeling** with proper relationships
- 🏗️ **Clean architecture** with separation of concerns

---

## 🏗️ Project Structure

```text
Building API/
├── app/                    # Original API version
├── app_v2/                 # Enhanced API version with comprehensive modeling
│   ├── models/             # SQLAlchemy database models
│   ├── routes/             # API endpoint handlers
│   ├── schemas/            # Pydantic validation schemas
│   ├── database.py         # Database configuration
│   └── main.py             # FastAPI application entry point
├── scripts/                # Data import utilities
├── data/                   # FHIR bundle data files
├── mock_data/              # Sample data for testing
├── tests/                  # Test suite
└── docker-compose.yml      # Docker configuration
```

---

## 🗃️ Comprehensive Data Modeling (app_v2)

### **Database Schema Overview**

The app_v2 implements a comprehensive healthcare data model with 6 core entities and their relationships:

#### **Core Entities:**

1. **🏢 Organizations** (`organizations_v2`)
   - Healthcare facilities, hospitals, clinics
   - Manages practitioners and hosts encounters
   - Contains contact and location information

2. **👥 Patients** (`patients_v2`)
   - Central entity - all healthcare data revolves around patients
   - Comprehensive demographic and contact information
   - Links to managing organization

3. **👨‍⚕️ Practitioners** (`practitioners_v2`)
   - Healthcare providers (doctors, nurses, specialists)
   - Belongs to organizations
   - Conducts encounters and performs observations

4. **🏥 Encounters** (`encounters_v2`)
   - Patient visits, appointments, hospital stays
   - Links patients, practitioners, and organizations
   - Contains visit details, timing, and reasons

5. **🩺 Conditions** (`conditions_v2`)
   - Medical diagnoses, problems, conditions
   - Associated with patients and encounters
   - Includes clinical status and verification

6. **📊 Observations** (`observations_v2`)
   - Clinical measurements, test results, vital signs
   - Links to patients, encounters, and practitioners
   - Supports both numeric and text values

### **Database Relationships & Cardinality**

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ PRACTITIONERS : "employs"
    ORGANIZATIONS ||--o{ ENCOUNTERS : "hosts"
    ORGANIZATIONS ||--o{ PATIENTS : "manages"
    
    PATIENTS ||--o{ ENCOUNTERS : "has"
    PATIENTS ||--o{ CONDITIONS : "has"
    PATIENTS ||--o{ OBSERVATIONS : "has"
    
    PRACTITIONERS ||--o{ ENCOUNTERS : "conducts"
    PRACTITIONERS ||--o{ OBSERVATIONS : "performs"
    
    ENCOUNTERS ||--o{ CONDITIONS : "diagnoses"
    ENCOUNTERS ||--o{ OBSERVATIONS : "includes"
```

### **Key Design Principles:**

#### **1. Patient-Centric Design**
- **Patients** are the central entity
- All clinical data (encounters, conditions, observations) links back to patients
- Enables comprehensive patient history and care coordination

#### **2. Flexible Relationships**
- **Optional foreign keys** allow for incomplete data scenarios
- **Nullable relationships** support real-world healthcare workflows
- **One-to-many relationships** follow healthcare domain patterns

#### **3. FHIR Compliance**
- **FHIR-style identifiers** for interoperability
- **Standardized coding systems** (LOINC, SNOMED CT)
- **Temporal data** with proper datetime handling

#### **4. Data Integrity**
- **Primary keys** with auto-incrementing IDs
- **Foreign key constraints** for referential integrity
- **Indexes** on frequently queried fields

### **Detailed Entity Specifications**

#### **🏢 Organizations Table**
```sql
CREATE TABLE organizations_v2 (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR UNIQUE,           -- FHIR identifier
    name VARCHAR NOT NULL,               -- Organization name
    type_code VARCHAR,                   -- Organization type (hospital, clinic, etc.)
    type_display VARCHAR,                -- Human-readable type
    phone VARCHAR,                       -- Contact phone
    email VARCHAR,                       -- Contact email
    address_line VARCHAR,                -- Street address
    city VARCHAR,                        -- City
    state VARCHAR,                       -- State/Province
    postal_code VARCHAR,                 -- ZIP/Postal code
    part_of_identifier VARCHAR           -- Parent organization
);
```

#### **👥 Patients Table**
```sql
CREATE TABLE patients_v2 (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR UNIQUE,           -- MRN/UUID from FHIR
    first_name VARCHAR NOT NULL,         -- Patient first name
    last_name VARCHAR NOT NULL,          -- Patient last name
    birth_date DATE NOT NULL,            -- Date of birth
    gender VARCHAR,                      -- Gender (M/F/O)
    phone VARCHAR,                       -- Contact phone
    email VARCHAR,                       -- Contact email
    address_line VARCHAR,                -- Street address
    city VARCHAR,                        -- City
    state VARCHAR,                       -- State/Province
    postal_code VARCHAR,                 -- ZIP/Postal code
    marital_status VARCHAR,              -- Marital status
    language VARCHAR,                    -- Preferred language
    race VARCHAR,                        -- Race
    ethnicity VARCHAR,                   -- Ethnicity
    deceased_date VARCHAR,               -- Date of death (ISO string)
    active BOOLEAN DEFAULT TRUE,         -- Active patient flag
    managing_organization_identifier VARCHAR  -- Managing organization
);
```

#### **👨‍⚕️ Practitioners Table**
```sql
CREATE TABLE practitioners_v2 (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR,                  -- FHIR identifier
    name VARCHAR NOT NULL,               -- Practitioner name
    gender VARCHAR,                      -- Gender
    specialty_code VARCHAR,              -- Medical specialty code
    specialty_display VARCHAR,           -- Specialty description
    phone VARCHAR,                       -- Contact phone
    email VARCHAR,                       -- Contact email
    organization_id INTEGER REFERENCES organizations_v2(id)  -- Employing organization
);
```

#### **🏥 Encounters Table**
```sql
CREATE TABLE encounters_v2 (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients_v2(id),
    practitioner_id INTEGER REFERENCES practitioners_v2(id),
    organization_id INTEGER REFERENCES organizations_v2(id),
    
    identifier VARCHAR,                  -- Encounter identifier
    status VARCHAR NOT NULL,             -- Encounter status (planned, active, finished)
    class_code VARCHAR,                  -- Encounter class (ambulatory, emergency, etc.)
    class_display VARCHAR,               -- Human-readable class
    start_time TIMESTAMP,                -- Encounter start time
    end_time TIMESTAMP,                  -- Encounter end time
    reason_code VARCHAR,                 -- Reason for encounter
    reason_display VARCHAR               -- Human-readable reason
);
```

#### **🩺 Conditions Table**
```sql
CREATE TABLE conditions_v2 (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients_v2(id),
    encounter_id INTEGER REFERENCES encounters_v2(id),
    
    code VARCHAR NOT NULL,               -- Condition code (ICD-10, SNOMED)
    system VARCHAR,                      -- Coding system
    display VARCHAR,                     -- Human-readable condition
    category_code VARCHAR,               -- Condition category
    clinical_status VARCHAR,             -- Clinical status (active, inactive, resolved)
    verification_status VARCHAR,         -- Verification status (provisional, confirmed)
    onset_time TIMESTAMP,                -- Condition onset time
    abatement_time TIMESTAMP,            -- Condition resolution time
    recorded_date TIMESTAMP              -- When condition was recorded
);
```

#### **📊 Observations Table**
```sql
CREATE TABLE observations_v2 (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients_v2(id),
    encounter_id INTEGER REFERENCES encounters_v2(id),
    practitioner_id INTEGER REFERENCES practitioners_v2(id),
    
    identifier VARCHAR,                  -- Observation identifier
    status VARCHAR NOT NULL,             -- Observation status
    code VARCHAR NOT NULL,               -- Observation code (LOINC)
    code_system VARCHAR,                 -- Coding system
    code_display VARCHAR,                -- Human-readable observation
    value_quantity FLOAT,                -- Numeric value
    value_unit VARCHAR,                  -- Unit of measurement
    value_string VARCHAR,                -- Text value
    effective_time TIMESTAMP,            -- When observation was taken
    issued_time TIMESTAMP                -- When observation was recorded
);
```

---

## 🧪 API Documentation

### **API Versions**
- **v1**: `/api/v1/*` - Original implementation
- **v2**: `/api/v2/*` - Enhanced version with comprehensive data modeling

### **Interactive Documentation**
Once running, open http://localhost:8000/docs for the interactive Swagger UI.

### **Health Check**
```bash
GET /api/v2/health
Response: {"status": "ok", "api": "v2"}
```

### **Example Endpoints (v2)**(implementing)

#### **Patients**
```bash
POST /api/v2/patients          # Create new patient
GET /api/v2/patients/{id}      # Get patient by ID
PUT /api/v2/patients/{id}      # Update patient
DELETE /api/v2/patients/{id}   # Delete patient
GET /api/v2/patients           # List all patients
```

#### **Encounters**
```bash
POST /api/v2/encounters        # Create new encounter
GET /api/v2/encounters/{id}    # Get encounter by ID
GET /api/v2/encounters         # List encounters (with filters)
```

#### **Conditions**
```bash
POST /api/v2/conditions        # Create new condition
GET /api/v2/conditions/{id}    # Get condition by ID
GET /api/v2/conditions         # List conditions by patient
```

#### **Observations**
```bash
POST /api/v2/observations      # Create new observation
GET /api/v2/observations/{id}  # Get observation by ID
GET /api/v2/observations       # List observations by patient
```

---

## 🗃️ Tech Stack

- **Backend Framework**: FastAPI 0.116.1
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Data Validation**: Pydantic
- **Containerization**: Docker + Docker Compose
- **API Documentation**: Swagger UI (OpenAPI)
- **Development Server**: Uvicorn

---

## 🚀 Quick Start

### **Prerequisites**
- Docker and Docker Compose
- Python 3.11+ (for local development)

### **Using Docker (Recommended)**
```bash
# Clone the repository
git clone https://github.com/adt6/Building-FastAPI.git
cd Building-FastAPI

# Start the services
docker-compose up -d

# The API will be available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### **Local Development**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python create_tables.py

# Run the application
uvicorn app_v2.main:app --reload
```

---

## 📊 Database Schema Visualization

View the complete database schema with relationships in the [Database UML Diagram](database_uml_diagram.puml).

---

## 🔧 Data Import

The project includes comprehensive data import scripts for loading FHIR bundle data:

```bash
# Import data from FHIR bundles
python scripts/import_patients_v2.py
python scripts/import_practitioners_v2.py
python scripts/import_encounters_v2.py
python scripts/import_conditions_v2.py
python scripts/import_observations_v2.py
python scripts/import_organizations_v2.py
```

---

## 🧪 Testing

```bash
# Run tests
pytest

# Test database connection
python test_db_conn.py
```

---

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


---

## 🤝 Acknowledgments

- Built following FHIR (Fast Healthcare Interoperability Resources) standards
- Inspired by real-world healthcare data management challenges
- Uses industry-standard technologies for healthcare applications




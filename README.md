# 🏥 FastAPI Healthcare API

A beginner-friendly, real-world FastAPI project for managing healthcare data using PostgreSQL and Docker. Built from scratch with clean architecture and RESTful CRUD endpoints for patients, practitioners, encounters, and conditions.

---

## 📦 Features

- 🚀 FastAPI backend with modular structure
- 🧠 SQLAlchemy ORM with PostgreSQL
- 📄 Pydantic for request/response validation
- 🐳 Docker + docker-compose for isolated development
- 🔁 CRUD endpoints for core FHIR-style entities
- 🔧 Swagger UI for interactive API testing

---

```markdown
## 🏗️ Project Structure

```text
app/
├── database.py           # SQLAlchemy engine/session
├── main.py               # FastAPI app entry point
├── models/               # SQLAlchemy models
├── routes/               # API endpoints
├── schemas/              # Pydantic schemas
└── utils/                # Utilities (optional)

mock_data/
├── patients.json
├── practitioners.json
├── encounters.json
└── conditions.json

```

---

## 🧪 API Documentation

Once running, open http://localhost:8000/docs for the interactive Swagger UI.

Example Endpoints:
POST /patients

GET /patients/{id}

PUT /patients/{id}

DELETE /patients/{id}

(Also available for practitioners, encounters, and conditions)

## 🗃️ Tech Stack

FastAPI

PostgreSQL

SQLAlchemy

Pydantic

Docker

Uvicorn

---




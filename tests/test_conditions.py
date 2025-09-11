from datetime import datetime, timezone


def ensure_patient(client) -> int:
    # Try to create a patient; if unique constraints existed we'd handle differently.
    payload = {
        "first_name": "Cond",
        "last_name": "Patient",
        "birth_date": "1990-01-01",
    }
    r = client.post("/api/v2/patients", json=payload)
    if r.status_code == 201:
        return r.json()["id"]
    # fallback: list and return first
    r2 = client.get("/api/v2/patients?limit=1")
    return r2.json()[0]["id"]


def test_list_conditions_ok(client):
    r = client.get("/api/v2/conditions?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_condition_201(client):
    patient_id = ensure_patient(client)
    payload = {
        "patient_id": patient_id,
        "code": "I10",
        "clinical_status": "active",
        "recorded_date": datetime.now(timezone.utc).isoformat(),
    }
    r = client.post("/api/v2/conditions", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["patient_id"] == patient_id
    assert body["code"] == "I10"
    client.created_condition_id = body["id"]


def test_get_condition_200(client):
    cid = getattr(client, "created_condition_id", None)
    assert cid is not None, "Create condition must run first"
    r = client.get(f"/api/v2/conditions/{cid}")
    assert r.status_code == 200
    assert r.json()["id"] == cid


def test_filter_conditions_by_patient(client):
    # List by patient_id should include only matching items
    cid = getattr(client, "created_condition_id", None)
    assert cid is not None
    # fetch created to get patient_id
    created = client.get(f"/api/v2/conditions/{cid}").json()
    pid = created["patient_id"]
    r = client.get(f"/api/v2/conditions?patient_id={pid}")
    assert r.status_code == 200
    for it in r.json():
        assert it["patient_id"] == pid



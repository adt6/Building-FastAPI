from datetime import datetime, timezone


def test_list_encounters_ok(client):
    r = client.get("/api/v2/encounters?limit=1")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_encounter_201(client):
    payload = {
        "patient_id": 1,
        "status": "completed",
        "start_time": datetime.now(timezone.utc).isoformat(),
    }
    r = client.post("/api/v2/encounters", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "completed"
    assert body["patient_id"] == 1
    assert "id" in body
    # store for subsequent tests
    client.created_encounter_id = body["id"]


def test_get_encounter_200(client):
    enc_id = getattr(client, "created_encounter_id", None)
    assert enc_id is not None, "Create test must run before get test"

    r = client.get(f"/api/v2/encounters/{enc_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == enc_id


def test_filter_by_patient_id(client):
    r = client.get("/api/v2/encounters?patient_id=1&limit=10")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    for it in items:
        assert it["patient_id"] == 1



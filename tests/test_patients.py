from datetime import date


def test_list_patients_ok(client):
    r = client.get("/api/v2/patients?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_patient_201(client):
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "birth_date": date(1995, 5, 20).isoformat(),
        "email": "alice@example.com",
    }
    r = client.post("/api/v2/patients", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["first_name"] == "Alice"
    assert body["last_name"] == "Smith"
    assert "id" in body
    client.created_patient_id = body["id"]


def test_get_patient_200(client):
    pat_id = getattr(client, "created_patient_id", None)
    assert pat_id is not None, "Create patient must run first"
    r = client.get(f"/api/v2/patients/{pat_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == pat_id


def test_update_patient_200(client):
    pat_id = getattr(client, "created_patient_id", None)
    r = client.put(f"/api/v2/patients/{pat_id}", json={"city": "NYC"})
    assert r.status_code == 200
    assert r.json()["city"] == "NYC"


def test_delete_patient_204(client):
    pat_id = getattr(client, "created_patient_id", None)
    r = client.delete(f"/api/v2/patients/{pat_id}")
    assert r.status_code == 204
    r2 = client.get(f"/api/v2/patients/{pat_id}")
    assert r2.status_code == 404





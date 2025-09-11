def test_health_ok(client):
    r = client.get("/api/v2/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "api": "v2"}



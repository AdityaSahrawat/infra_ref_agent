from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_openapi_has_action_routes() -> None:
    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json().get("paths", {})

    # actions endpoints
    assert "/incident/actions" in paths
    assert "/incident/actions/{action_id}" in paths
    assert "/incident/{incident_id}/actions" in paths

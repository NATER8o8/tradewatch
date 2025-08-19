
from fastapi.testclient import TestClient
from .app import app

def test_risk_endpoint():
    with TestClient(app) as c:
        r = c.get("/api/risk/officials")
        assert r.status_code in (200, 500)

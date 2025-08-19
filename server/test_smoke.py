
from fastapi.testclient import TestClient
from .app import app

def test_healthz():
    with TestClient(app) as c:
        r = c.get("/healthz")
        assert r.status_code == 200
        assert "ok" in r.json()

def test_routes_exist():
    with TestClient(app) as c:
        assert c.get("/api/trades").status_code in (200,403,500)  # may 500 if DB not ready
        assert c.get("/api/export/backtest.json").status_code in (200,500)

def test_search_endpoint():
    with TestClient(app) as c:
        r = c.get("/api/search", params={"q":"AAPL"})
        assert r.status_code == 200

import pytest
from fastapi.testclient import TestClient
from fleet_catalog.api import create_app
from fleet_catalog.models import utcnow


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("CATALOG_API_TOKEN", raising=False)
    app = create_app("sqlite:///" + str(tmp_path / "api.db"))
    with TestClient(app) as c:
        yield c


def test_catalog_and_impact_end_to_end(client):
    assert len(client.get("/api/catalog").json()["entities"]) == 27
    assert len(client.get("/api/impact/node:FTL-A11").json()["services"]) == 4
    assert client.get("/api/impact/node:unknown").status_code == 404


def test_scenario_persists_and_export_is_downloadable(client):
    assert client.post("/api/catalog/scenarios/ownership-conflict").status_code == 200
    data = client.get("/api/catalog").json()
    assert any(
        i["code"] == "owner_conflict" for e in data["entities"] for i in e["issues"]
    )
    r = client.get("/api/catalog/export/backstage")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert client.post("/api/catalog/scenarios/refresh").status_code == 200
    assert not any(e["issues"] for e in client.get("/api/catalog").json()["entities"])


def test_bad_sync_cannot_partially_mutate_database(client):
    r = client.post(
        "/api/sources/kubernetes/sync",
        json={
            "batch_id": "invalid",
            "observed_at": utcnow().isoformat(),
            "records": [
                {
                    "external_id": "x",
                    "entity_id": "service:x",
                    "kind": "node",
                    "fields": {},
                }
            ],
        },
    )
    assert r.status_code == 409
    assert len(client.get("/api/catalog").json()["entities"]) == 27


def test_token_enforcement(client, monkeypatch):
    monkeypatch.setenv("CATALOG_API_TOKEN", "test-token")
    assert client.get("/api/catalog").status_code == 401
    assert (
        client.get(
            "/api/catalog", headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/api/catalog", headers={"Authorization": "Bearer test-token"}
        ).status_code
        == 200
    )
    assert client.get("/health").status_code == 200


def test_request_size_limit(client):
    assert (
        client.post(
            "/api/sources/kubernetes/sync", content="x" * (4 * 1024 * 1024 + 1)
        ).status_code
        == 413
    )

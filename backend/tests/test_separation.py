from fastapi.testclient import TestClient
from fleet_catalog.api import create_app
from fleet_catalog.models import Base


def test_catalog_has_only_catalog_tables_and_routes(tmp_path):
    with TestClient(create_app("sqlite:///" + str(tmp_path / "catalog.db"))) as client:
        assert client.get("/api/pipeline").status_code == 404
        assert client.post("/api/runs", json={}).status_code == 404
        assert set(Base.metadata.tables) == {
            "sources",
            "observations",
            "entities",
            "sync_runs",
            "audit",
        }

import httpx
from fastapi.testclient import TestClient
from fleet_catalog import ui
from fleet_catalog.api import create_app


def test_gradio_catalog_uses_reconciled_api(tmp_path, monkeypatch):
    with TestClient(create_app("sqlite:///" + str(tmp_path / "ui.db"))) as api:

        class Bridge:
            def __init__(self, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url):
                return api.get(url.removeprefix("http://127.0.0.1:8002"))

            def post(self, url, json):
                return api.post(url.removeprefix("http://127.0.0.1:8002"), json=json)

        monkeypatch.setattr(httpx, "Client", Bridge)
        monkeypatch.delenv("CATALOG_API_URL", raising=False)
        monkeypatch.delenv("CATALOG_API_TOKEN", raising=False)
        monkeypatch.setattr(ui, "REPORTS", tmp_path / "exports")
        data, summary, *_ = ui.refresh()
        assert len(data["entities"]) == 27 and ">96<" in summary
        details, provenance, exposure, graph = ui.inspect("node:FTL-A11", data)
        assert (
            details["kind"] == "node" and provenance and len(exposure["services"]) == 4
        )
        assert ui.apply_fixture("ownership-conflict")[-1]
        assert (
            "backstage.io"
            in __import__("pathlib").Path(ui.export_catalog()).read_text()
        )
        app = ui.build_app()
        assert len([c for c in app.config["components"] if c["type"] == "tabitem"]) == 4


def test_unavailable_catalog_is_explicit(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(ui, "request", fail)
    assert "unavailable" in ui.refresh()[1]

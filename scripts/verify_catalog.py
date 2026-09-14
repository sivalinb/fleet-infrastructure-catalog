"""Verify catalog reconciliation through real HTTP and the Gradio API."""

import json
import time
from pathlib import Path

import httpx
from gradio_client import Client


def main():
    with httpx.Client(base_url="http://127.0.0.1:8002", timeout=20) as api:
        for _ in range(60):
            try:
                if (
                    api.get("/health").is_success
                    and httpx.get("http://127.0.0.1:7861/config").is_success
                ):
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Catalog stack unavailable")
        assert api.get("/api/pipeline").status_code == 404
        assert api.get("/api/runs/example").status_code == 404
        api.post("/api/catalog/scenarios/refresh").raise_for_status()
        baseline = api.get("/api/catalog").raise_for_status().json()
        assert len(baseline["entities"]) == 27
        checks = {"baseline_entities": True, "no_telemetry_routes": True}
        ui = Client("http://127.0.0.1:7861", verbose=False)
        ui.predict(api_name="/refresh_catalog")
        ui.predict("ownership-conflict", api_name="/apply_fixture")
        conflict = api.get("/api/catalog").json()
        checks["conflict_from_gradio"] = any(
            i["code"] == "owner_conflict"
            for e in conflict["entities"]
            for i in e["issues"]
        )
        exposed = api.get("/api/impact/node:FTL-A11").json()
        checks["four_exposed_services"] = len(exposed["services"]) == 4
        export = ui.predict(api_name="/export_catalog")
        checks["backstage_export"] = (
            "apiVersion: backstage.io" in Path(export).read_text()
        )
        ui.predict("refresh", api_name="/apply_fixture")
        checks["restore"] = not any(
            e["issues"] for e in api.get("/api/catalog").json()["entities"]
        )
        checks["audit"] = bool(api.get("/api/audit").json())
        assert all(checks.values()), checks
        out = Path("evidence")
        out.mkdir(exist_ok=True)
        (out / "integration.json").write_text(
            json.dumps(
                {"checks": checks, "entities": 27, "modeled_gpu_slots": 96}, indent=2
            )
            + "\n"
        )
        print("Catalog HTTP, reconciliation, impact, audit, and Gradio export passed")


if __name__ == "__main__":
    main()

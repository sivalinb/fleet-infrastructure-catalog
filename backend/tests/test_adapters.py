import pytest
from fleet_catalog.adapters import kubernetes_records, redfish_records


def test_kubernetes_parser_uses_serial_identity():
    r = kubernetes_records(
        {
            "items": [
                {
                    "kind": "Node",
                    "metadata": {
                        "name": "new-hostname",
                        "annotations": {"fleet_catalog/serial": "FTL-1"},
                    },
                    "status": {"conditions": [{"type": "Ready", "status": "True"}]},
                }
            ]
        }
    )[0]
    assert r.entity_id == "node:FTL-1" and r.fields["health"] == "healthy"


def test_kubernetes_parser_rejects_missing_serial():
    with pytest.raises(ValueError):
        kubernetes_records({"items": [{"kind": "Node", "metadata": {"name": "host"}}]})


def test_redfish_parser_maps_health_and_identity():
    r = redfish_records(
        {
            "Id": "server1",
            "SerialNumber": "FTL-1",
            "Status": {"Health": "Warning"},
            "Oem": {"FleetLab": {"gpus": 8}},
        }
    )[0]
    assert (
        r.entity_id == "node:FTL-1"
        and r.fields["health"] == "degraded"
        and r.fields["gpus"] == 8
    )


def test_redfish_parser_rejects_missing_serial():
    with pytest.raises(ValueError):
        redfish_records({"Id": "server1"})

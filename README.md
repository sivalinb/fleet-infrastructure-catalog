# Fleet Infrastructure Catalog

**Know what you operate, who owns it, and where the evidence came from.**

A Python infrastructure catalog by [Siva Babu](https://github.com/sivalinb). It reconciles source observations into canonical hardware, service, and team identities, while preserving provenance, conflicts, freshness, and lifecycle changes.

![Reconciliation architecture](docs/assets/reconciliation.svg)

## Capabilities

- Normalize Kubernetes and Redfish snapshot records into stable identities.
- Choose authoritative values per field while retaining conflicting owner evidence.
- Detect stale sources, missing owners, absent records, and dangling dependencies.
- Trace dependency exposure from clusters, racks, and nodes to services and owners.
- Inspect source quality and audit history through Gradio; export Backstage catalog YAML.
- Persist state in SQLite or PostgreSQL with idempotent, transactional source imports.

The included inventory is fictional: 2 clusters, 4 racks, 12 nodes, 6 services, 3 teams, and 96 modeled GPU slots. Import adapters consume supplied snapshots; continuous live source polling is not implemented. The separate [Telemetry Reliability Lab](https://github.com/sivalinb/fleet-telemetry-lab) owns telemetry experiments and is not a runtime dependency.

## Installation

Python 3.12 is recommended; Python 3.11+ is supported.

```sh
git clone https://github.com/sivalinb/fleet-infrastructure-catalog.git
cd fleet-infrastructure-catalog
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
python scripts/run_stack.py
```

The application listens on `127.0.0.1:7861`; the API reference is at `127.0.0.1:8002/docs`. Ctrl-C stops owned processes. The catalog needs no telemetry backend, GPU, or cloud credentials.

`docker compose up --build` provides a PostgreSQL deployment with separate catalog volumes. Published ports bind to loopback. [Source adapters](fixtures/README.md) document supported snapshot fields and import semantics.

## Verification

```sh
python -m pytest
python scripts/ci_integration.py
```

The integration command owns a temporary application process lifecycle on the standard catalog ports. CI also verifies PostgreSQL reconciliation and restart persistence. [Test cases](docs/TESTING.md) cover correctness and failure boundaries.

## Implementation

| Area | Code |
| --- | --- |
| Gradio interface | [ui.py](backend/fleet_catalog/ui.py) |
| API and authorization | [api.py](backend/fleet_catalog/api.py) |
| Identity and reconciliation | [catalog.py](backend/fleet_catalog/catalog.py) |
| Source normalization | [adapters.py](backend/fleet_catalog/adapters.py), [import_source.py](scripts/import_source.py) |
| Storage and fixtures | [models.py](backend/fleet_catalog/models.py), [fixtures.py](backend/fleet_catalog/fixtures.py) |

[Overview](docs/OVERVIEW.md) · [Architecture](docs/ARCHITECTURE.md) · [Technologies](docs/TECHNOLOGIES.md) · [Scaling](docs/SCALING.md) · [Extensions](docs/EXTENSIONS.md) · [HTML overview](docs/keynote.html)

# Technologies

| Technology | Responsibility |
| --- | --- |
| Python | Reconciliation, import adapters, API, interface, and verification |
| FastAPI and Pydantic | HTTP endpoints, request validation, typed import contracts |
| SQLAlchemy | Transactions and persisted observations, entities, and audit history |
| SQLite / PostgreSQL | Local storage / container and CI storage |
| Gradio and Plotly | Catalog interface and relationship graph |
| HTTPX | Source snapshot retrieval and API access |
| PyYAML | Backstage-compatible catalog export |
| pytest and GitHub Actions | Regression, HTTP, interface, and database verification |

Kubernetes and Redfish inputs are normalized snapshots. Backstage output is YAML generation; a Backstage server is not bundled. All application code is Python.

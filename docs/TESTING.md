# Verification

Unit and API tests cover identity reconciliation, per-field authority, conflicting owners, missing owners, dangling references, source freshness, entity retention, cycle-safe dependency traversal, import replay, stale snapshots, invalid timestamps, rollback, API tokens, and request size limits.

Adapter tests verify serial-based identity, health mapping, and rejection of incomplete source records. Interface tests use the real API behind Gradio functions. A separation regression checks that only catalog tables and routes exist.

`python scripts/ci_integration.py` starts an independent catalog API and Gradio application, applies an ownership conflict through the Gradio API, checks dependency exposure, exports Backstage YAML, restores fixtures, and validates audit persistence. It stops its owned processes on exit.

`scripts/verify_postgres.py` uses an explicitly configured disposable PostgreSQL database and verifies reconciliation and restart persistence. GitHub Actions runs this separately from local SQLite checks.

JUnit and integration records are written under `evidence/`. No telemetry service is needed for these checks. A passing suite covers the supplied fixtures and tested boundaries; it is not a capacity benchmark.

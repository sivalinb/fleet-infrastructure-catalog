# Operational reference

Source age is evaluated against its configured TTL. A stale source makes current state uncertain; it does not establish a hardware failure. A missing source record retains identity and history. Owner conflicts preserve the resolved authority and the conflicting observation.

For import errors, inspect the HTTP response, batch identifier, canonical identity, and observation timestamp. An older snapshot cannot roll back newer source state. Reused batch IDs must retain exactly the same payload. Fixture restoration replaces fictional source values and should not be used to maintain manually imported inventory.

The process launcher records owned PIDs in `.runtime/processes.json` and logs under `.runtime/logs`. SQLite state is `.runtime/catalog.db`; container PostgreSQL uses the catalog volume. Back up persisted data before changing schemas or storage configuration.

# Scaling

The current implementation rebuilds the full entity projection after an import and serves the relationship graph as one response. That keeps the reconciliation rules inspectable, but costs grow with observations and edges. No fleet-size throughput claim is made.

At larger scale, move ingestion to durable jobs, serialize or partition reconciliation by canonical identity, and update only affected projections. Add database migrations, index measured query paths, paginate entity and audit APIs, and bound dependency traversal. Preserve source timestamps, import digests, tombstones, and provenance through these changes.

Independent source workers need checkpoints, retry budgets, full-snapshot completeness checks, and explicit backpressure. A partial page must never be treated as a complete source snapshot. A periodic freshness job should update the view even when no new import arrives.

Benchmark with fixed entity and observation counts, realistic update skew, dependency fan-out, conflicting fields, concurrent readers, and process restarts. Record import throughput, p95 query latency, database growth, reconciliation lag, and recovery behavior. Add tenancy and per-source authorization before sharing an instance across teams.

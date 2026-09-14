# Infrastructure ownership with source evidence

An infrastructure object can appear under multiple source identities. A hostname may change while a hardware serial remains stable; two systems may disagree about its owner. A catalog that silently takes the latest value hides information needed for support and incident response.

This project stores observations separately from the resolved entity. The projection makes common lookups convenient while retaining the source and observation time for each field. Conflicts, missing references, and stale observations remain visible.

The relationship graph connects clusters, racks, nodes, services, and teams. Dependency exposure identifies related services and owners. It does not predict that every related service will fail.

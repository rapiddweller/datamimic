# Amendment 67: Domain-owned identifier allocation

Date: 2026-09-29. Decision: reviewer after Astra's ownership review.

The target declared `BaseDomainService` but omitted the stateful identifier
allocation contract it shares with Runtime. Declare `IdentifierRegistry` through
`domains.api` and under its physical `domain_core` owner. Runtime owns the
register's lifetime; Domains owns collision handling and its private state.
No plain-dictionary compatibility path or new component is added.

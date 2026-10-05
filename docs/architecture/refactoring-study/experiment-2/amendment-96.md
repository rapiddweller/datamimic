# Amendment 96: Runtime and IO namespace owners

2026-10-05. Astra, delegated architect; base `01f9a324`.

The Runtime and IO initializers contain only responsibility docstrings.
Their existing API components own those package entry markers, following
Amendment 94's Domain decision. Published ArchKeel 0.9.0 now measures these
previously omitted inner assignments.

Add `datamimic_ce.engine.runtime` to RUNTIME-API and
`datamimic_ce.engine.io` to IO-API using `exact_modules`, not package prefixes.
State marker ownership in each existing responsibility sentence. Keep every
child owner, public interface, dependency permission and rule unchanged.

No source, XML, baseline, budget, allowance, oracle, gate or checker edits.
The other ten initializer findings require separate concern decisions;
this amendment does not silently assign them to convenient leaf components.

Evidence: [Step 104](step-104-runtime-io-owners.md), independent Luna inspection
and QA, and complete released-checker before/after observations.

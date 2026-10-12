# Amendment 199 — process-local clients

**Decision:** user-defined process boundary, refined by Astra after the
single-process clarification. This supersedes D11's eager client registration
and the lifecycle-preservation condition in edition-alignment; historical
evidence remains unchanged. It declares the target, not implemented acceptance.

## Execution ownership

- Ordered setup registers existing typed connection configurations, not clients.
- Main executes serial setup SQL, source counting, sequence preparation and
  single-process generation. It is the worker for those phases; no extra process.
- Each executing process creates and reuses its own clients through IO.
  Runtime coordinates cleanup; IO releases resources owned by that execution.
  Cleanup must preserve an active task exception and leave caller-owned injections
  alone.
- Parallel workers receive configurations and required native execution state.
  Client instances, connections, engines and client-bearing aliases/captures
  never cross that boundary, including through inherited process state.
- Worker projection is separate from same-process include cloning. Preserve
  required Memstore inputs, scripts, seeds, demographics and prepared generators;
  do not replace native values with JSON or guess dependencies from script names.

The existing Runtime contexts/lifecycle/setup/generate and IO clients components
own this work. Their contracts carry this decision in responsibilities and
provenance. No new component, dependency permission, proxy or public API is added.
Generate orchestration still cannot connect clients directly: serial preparation
delegates source/connection work through the existing IO boundaries.

## Compatibility and acceptance

Preserve descriptor order, source-count/error timing, exactly-once sequence
reservation, native rows, script alias identity and existing result channels.
[Amendment 155](amendment-155-execute-task-sql-capability.md) remains binding for
main/serial injected SQL clients: one direct lookup/call and native failures.
Child-required custom clients or hidden captured references need an explicitly
supported reconstruction contract; arbitrary payload compatibility is UNKNOWN.
Do not silently transfer them or force serial execution.

1. Implement the complete descriptor-owned config → local client → client-free
   child transfer → owned cleanup path, including source and target consumers.
2. Verify real process IDs, aliases, count/setup/sequence ordering, failure cleanup,
   include scoping, Memstore readback and helper/cached-generator controls.
   Prove isolation for the selected start method; serialized fields alone do not
   prove isolation under fork. Spawn is a candidate, not an accepted behavior change.
3. Compare supported DSL behavior against the original revision; record approved
   construction/cleanup differences separately. Test optional Ray independently.

Static import rules do not enforce creation PID, captured object graphs or cleanup.
Definition checks prove coherent declarations only. Service-backed runtime proof
is required; no PASS claim follows from this amendment.

## Evidence

At `586a36f2`, setup constructs wrappers, Context copies clients and namespace,
and Generate dispatches that copy without configuration-based worker construction.
Connection laziness does not satisfy client ownership. [CE #289](https://github.com/rapiddweller/datamimic/issues/289)
contains commit-pinned source links. No socket transfer, leak or cause of #281 is established.

The 42-file static audit was independently checked. Its earlier recommendation
to move all serial work into an extra process is rejected by the user's clarification.
Source audit SHA256: `92a1a3a20d405878a6e47d39a920fdac70a07bbfc9f968997ee4531ae6fe8c83`.
Independent QA SHA256: `2b3657a4c33dbc3bc22b4cdbf3e6d0cd133dab87affb8ae6e8b90db2b92fa5ed`.

LOCAL VERIFIED: source/contract review, `make architecture-definition-check`
(13 passed), and `make architecture-report` with 488/488 parsed files. Report
remains `declared_rules: FAIL`, with 13 violations and 200 measured UNKNOWN
positions; no ownership-specific runtime proof follows. CI-ONLY VERIFICATION:
`586a36f2` has 50 successes, four architecture failures and four skips;
neither service-suite success proves process ownership nor clears architecture debt.

# Step 54: publish Runtime demographic context

`SetupContext` already accepts, returns and sets `DemographicContext`. Runtime now
re-exports the existing class; the owning root and inner components already
publish its modules. No behavior or descriptor changed.

The context's transaction override is intentionally an open weighted mapping.
[Amendment 70](amendment-70.md) names its three exact nested positions. The
updated ArchKeel candidate classifies proven `Mapping` as broad and keeps its
member UNKNOWNs; no generic UNKNOWN is silently treated as PASS.

Latest candidate report: 491/491 files scanned, 109 violations, 170 UNKNOWN
positions, 2 package-cycle edges (domains/engine roll-up; no module cycle
crosses them). This is not a green target gate. Compared with the prior 94
violations, the increase is primarily new Mapping findings from the stronger
checker, not proof that the CE implementation regressed.

LOCAL VERIFIED: 1,484 unit tests passed (11 skipped, 1 xfailed); 7 focused
architecture tests and the demographic integration test passed; Ruff, full
package MyPy and `git diff --check` passed. The full descriptor oracle was not
rerun for this re-export; CI was not run.

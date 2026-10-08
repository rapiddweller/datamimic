# Step 29: type the CE client path

`SetupContext` now keeps its existing eager client registration, lookup and
worker-copy behavior behind `dict[str, Client]`. `<execute type="sql">` still
selects the target in Runtime, but IO checks the client capability and executes
the SQL. Missing targets still raise `KeyError`; a non-RDBMS target still raises
`AttributeError` at execution. The public DSL description was left unchanged.

LOCAL VERIFIED: 1,429 unit tests pass (11 skipped, 1 expected failure), 38
focused context/SQL/integration/architecture tests pass, Ruff and full-package
MyPy pass, and Pylint reports no executable import cycle. Independent QA added
positive and negative SQLite, namespace, client-copy and rollback checks.
The four Authoring/capability projection hashes match Step 27 exactly.

The fresh ArchKeel report observes 489/489 modules. It has 119 violations
(Step 28: 118) and 235 measured UNKNOWN positions (Step 28: 237). The old two
open client-map type messages became three more explicit `dict[str, Client]`
messages, including the newly annotated setter; no new dependency violation
appeared. This is not a green ratchet: baseline validation is still UNKNOWN
with 13 inherited-generic `interface.unused` diagnostics (ArchKeel #204) and
`baseline_new=89`. The exact open-map allowance remains tracked in #207.
No full descriptor comparison or external-service run was repeated for this
step, so behavioral equivalence is not yet established.

CE's eager-client lifecycle is not EE's lazy configuration-first lifecycle;
the shared target paths do not imply identical timing.
CI-ONLY VERIFICATION: not run. This step remains provisional and uncommitted.

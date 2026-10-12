# Amendment 180 — exact Runtime capture selectors

2026-10-10. Decision: Astra, delegated architect. Base `cd6b1666`.

Runtime owns the execution result shape; IO owns its live capture collection.
DSL captures include native scalar and mapping rows. Preserve their order and
dictionary/list/row identity at the result boundary, and `None` outside test
mode. Fixed execution controls remain typed; no production or EE code changes.

Amendment 99 retained these semantics but explicitly withheld type permissions.
This new decision supersedes that freeze only for `runtime.api.run`'s
`return.captured`, replacing Amendment 82's three obsolete selectors with:

| Complete annotation | Container depth |
| --- | --- |
| `dict[str, list[object]] \| None` | omitted; outer-map permission |
| `dict[str, list[object]] \| None` | 2; native row permission |

Both entries belong to `RUNTIME-API-TYPES`, qualified name
`datamimic_ce.engine.runtime.api.run`, position `return`, field path `captured`.
The rule remains agent-decided. This is an explicit target widening and accepted
opacity; it does not prove type closure or serializability. Amendment 99's
factory-overlay rules and compatibility limits remain unchanged.

Expected delta: only `VIO-3f809c5022ec9797` and `VIO-34ec78829affde2d` disappear
(55 → 53); `run.request.platform_props` stays red. Keep all other findings,
254 canonical UNKNOWNs, ownership, dependencies, baseline, budgets and oracle.
Evidence: `/tmp/ce-resume-20261010/next-slice-165/`.

LOCAL VERIFIED: both revised contract guards fail against the old contract and
remain byte-identical for the green run; all 62 Runtime boundary tests pass.
They exercise real XML captures, native identity/order, disabled capture and
factory-overlay errors. The 13 definition checks, Ruff and full MyPy (488 files)
pass. Fresh ArchKeel 1.1.0 report: 53 findings, Runtime 10 → 8, unchanged 200
measured UNKNOWN positions and 488/488 parsed files. Declared rules remain FAIL.

Independent QA confirms only the two named findings disappear; the other 53
findings and all 254 canonical UNKNOWN records remain exact. Two allowance
facts are added; ten existing Runtime facts change only Amendment provenance.
Nine matcher controls and one real source fixture pass: incorrect coordinates
restore the expected findings, and `request.log_level: object` stays red.

Native amendment validation against `cd6b1666` exits 2 with the same 19
`interface.usage_unknown` diagnostics and 31 baseline-new groups. It retains
the Runtime `allowed_positions` widening but emits no amendment artifact:
machine binding remains open. Full DSL/EE acceptance is not established.

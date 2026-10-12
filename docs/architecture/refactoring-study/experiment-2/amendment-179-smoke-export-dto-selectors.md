# Amendment 179 — exact smoke-export DTO selectors

2026-10-10. Decision: Astra, delegated architect. Base `cb1a09e9`.

Amendments 62/72 already accept native smoke-export rows and exporter options.
IO owns export and option validation; Authoring owns the captured rows it sends.
The fields remain `params: dict[str, object]` and `rows: list[dict[str, object]]`.
No production code or behavior changes.

Published ArchKeel 1.1.0 supports exact DTO-field declarations with native-value
depth. Correct only `IO-API-TYPES`, callable
`datamimic_ce.engine.io.api.smoke_export`, position `request`:

| Field | Complete annotation | Container depth |
| --- | --- | --- |
| params | `dict[str, object]` | omitted; existing outer-map permission |
| params | `dict[str, object]` | 1 |
| rows | `list[dict[str, object]]` | omitted; outer-map permission |
| rows | `list[dict[str, object]]` | 2 |

This replaces three stale selectors and lifts the prior DTO/depth hold only for
these two fields. It is a target correction and accepted opacity, not source-debt
reduction or proof of serialization/type closure. Other methods, fixed controls,
Runtime captured values, aliases and general iterables remain constrained.
IO retains agent attribution. Ownership, public/dependency grants, baseline,
oracle and all production bytes remain unchanged.

Expected delta: remove only `VIO-e700983c392af02a`, `VIO-f6535180ad421b1f` and
`VIO-9e2e02bff5f37d7c`; retain the other 55 findings and 254 canonical UNKNOWNs.
Contract widening and any refused machine amendment remain explicit evidence.

Verified with published 1.1.0: 58 → 55 findings (IO 34 → 31), 200 measured
UNKNOWN positions, unchanged source digest and 488/488 parsed files. The 36
IO/smoke-export/caller tests and 13 definition checks pass; Ruff and full MyPy
(488 files) pass. No new full DSL/EE proof is claimed.

Independent native comparison confirms only the three named findings disappear;
the other 55 findings, all 254 canonical UNKNOWNs and the component structure
remain unchanged. Three exact allowance facts are added. Nine negative controls
restore the expected findings for incorrect coordinates, omitted grants or a
broadened fixed control; payload permissions never exempt `basename`.

Native `validate --against cb1a09e9 --write-amendment` exits 2: all 19 diagnostics
are `interface.usage_unknown`; 31 baseline-new groups remain. The report retains
one `ir.widening` for IO's `allowed_positions`, but emits no amendment artifact.
Astra's decision is documented; machine binding remains open. The baseline is
unchanged. Evidence: `/tmp/ce-resume-20261010/`.

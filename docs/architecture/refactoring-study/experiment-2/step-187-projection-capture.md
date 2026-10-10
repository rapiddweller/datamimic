# Step 187 — four public projection comparisons

Original `a219163e` and current `7e9e8973` each ran the same current projection
recorder once. Six native CLI calls exited zero with empty stderr. Independent
QA accepts these bounded results:

| Projection | Result |
|---|---|
| Authoring reference | Byte-identical |
| Scaffold reference | Byte-identical |
| Compiler XML | Byte-identical |
| Full capabilities | APPROVED_DIFFERENCE |

Capabilities differ only at seven [Amendment 60](amendment-60.md) strings:
four generate/iterate sourceEntity/targetEntity descriptions, variable's type
description and DM401/DM402 provenance. The eighth logical path is the
[declared transition attributes](amendment-2026-09-29-transition-grammar.md).
All other JSON content and types match. The [receipt](step-187-projection-capture-receipt.json)
retains exact before/after values and approvals.

The unchanged historical comparator still returns **FAIL** across revisions:
its unequal-content bridge requires old metadata `4.3.1.dev89+dirty`, while
both actual captures truthfully report the shared installed version
`4.3.1.dev246+dirty`. Both self-comparisons pass; five evidence-corruption
controls reject. Neither versions nor the predicate were altered. Astra
accepts the finite approved differences separately from this retained FAIL.

Only the original compiler import is rebound. Inputs, commands, model and
serialization are identical. Clone-local origins, shared metadata location,
100 dependency versions, raw streams and persistent cleanup are pinned.
Environment values, historical environment, dotenv startup, transient effects,
native scope diagnostics, entity pages, lint/transport and EE remain outside
this slice. The owner ledger and historical oracle are unchanged.

LOCAL VERIFIED: raw projection bytes, exhaustive content delta, unchanged
comparator results, five negative controls and independent QA. Ruff and full
MyPy pass (488 files). CI-ONLY VERIFICATION: none for these local comparisons.
These four results do not complete protocol item 6 or full CE/EE acceptance.

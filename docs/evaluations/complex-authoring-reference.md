# Complex human-first authoring reference

This is the required complex reference case for agent-authoring changes. It is
an evaluation brief, not a claim that the supplied EE project runs unchanged in
CE. Use the original reference project supplied for the evaluation; retain its
revision/hash, inputs, original requirements and all attempts outside the repo.
Do not copy customer data or connection configuration into the plugin.

## Fixed task

Preserve eleven target tables and their 27 existing columns. The standard case
has 100 people, ten companies, eleven approvals, 22 approval versions and 82
staffing rows: 540 rows across the full target contract. No extra rule tables,
runtime AI or custom rule framework. Rule parameters, demand and master data
have separate responsibilities and one authoritative owner each.

| Rule | Required positive and negative controls |
|---|---|
| R1 | Employment must match person, company and function; break each component |
| R2 | Required active base license; reject missing, expired and inactive licenses |
| R3 | Required active additional qualification; reject its absence |
| R4 | Demand within maximum; different people fill different seats of one version/position |
| R5 | Approval exclusivity distinguishes approvals while versions share their approval |
| R6 | Company exclusivity permits reuse within one company and rejects cross-company reuse |

Resolve company through the approval's addressee. A license is valid on its
expiry date; missing expiry is not unlimited validity. Include a case that needs
backtracking, one proven infeasible case and one exhausted search budget. Budget
exhaustion must not be called infeasible. Repetition preserves input data and
produces the same plan for the same model, inputs, seed and clock.

## Executable review surface

The entry model exposes data preparation, validation, suitability, complete
assignment, export validation, cleanup and export in order. Native field
operations carry types, conditions, relationships, weights and target projection.
Every added field/file/helper has a named consumer. Python is a small named,
typed algorithm for global search, receiving prepared candidates/demand/policy
and returning the plan and decision evidence. Avoid hiding field operations or
data access inside a generic record wrapper or a second rule engine.

A human can locate each rule and its parameter source, change it and inspect its
impact. The decision trace includes names, rule values and exclusion reasons.
Complete output is validated before cleanup. Record the actual transaction
boundary; planning-before-cleanup does not prove atomic cleanup and export.

## Evidence and acceptance

Retain exact compiled XML, supporting files, unmodified tool receipts and a
requirement-to-evidence review. Check semantic DM JSON/XML roundtrips, positive
and negative runtime cases, all target columns/counts/joins, complete readback,
replay and the delivered archive. Static checks, bounded captures, actual
runtime delivery and full business acceptance have separate results.

Report every unsupported operation without weakening the task. CE's bounded
Python-loading boundary is tracked in [#332](https://github.com/rapiddweller/datamimic/issues/332).
Edition-specific syntax/capability alignment belongs to
[#270](https://github.com/rapiddweller/datamimic/issues/270). An EE test result or a
minimal compile probe cannot satisfy the full CE reference gate. Missing CE
runtime evidence leaves this gate open, even if setup and simpler models pass.

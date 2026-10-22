# Agent diagnostics round 2 review (#355 items 1, 3, 4, 7, 8, 9 and #373)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/agent-diagnostics-round-2`, base `6d09db1a` (origin/development), head `3e5d0eb9` (three commits).
- This review rebinds the [#271/#272 receipt](pr-271-272-missing-source-control-events-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** Source and Validation digests. The new values are in `completion-unknowns.json`.
- **Validation** moved only through coverage counts: 13,378 → 13,401 calls analysed.
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the 313 UNKNOWN records (same ids, same digest) and the 20 `interface.usage_unknown` diagnostics.
- **Measurements:** 1,424 unresolved calls, 178 typing positions, 255 unknown positions, 0 violations.

## Source review

**Row conditions (items 3 and 8).**
- The budgets are named constants. One string, `ROW_CONDITION_GRAMMAR`, publishes the operators, the operands and every budget, including the 1,024-character string limit. The `condition` field description reuses it.
- `_OPERATORS` is keyed by node type, so dispatch stays on types.
- A failed evaluation now carries a typed `RowConditionFailure` reason:
  - missing value;
  - unsupported value;
  - over budget;
  - type mismatch;
  - arithmetic.
- **No behaviour change for conditions that used to evaluate.** The new `try` blocks around the `BinOp` operator and the `Compare` operation only relabel exceptions that already ended in "could not be evaluated".
  - `operation is not None and operation(...)` is equivalent to the old `operation is None or not operation(...)`.
  - `RowConditionError` is a `ValueError`, so the pydantic parse path and `acceptance_contract` behave as before.

**Named rejections.**
- **Item 1:** a duplicate product is rejected at the second product's own `properties/name` path.
- **Item 4:** `values=` gets a quoted-literal remediation, and both model descriptions now say quoted literals.
- **#373:** ambiguous role pairs get their own remediation, separate from missing ones.
- **Item 9, steps only:** a bounded-policy refusal inside an included step is reported at `include/<uri>/<tag>`. This matches the runtime convention for steps. A refusal in the entry keeps the base path `descriptor/<entry>`, with no tag. That is deferred by decision, and the PR states it.

**DM316 (item 7).**
- The first head advised against `cyclic` in general. That was false: a cyclic file source with count 5 over 3 rows, and a cyclic `iterate` with count 7, both Build `ready`.
- `3e5d0eb9` restricts the warning to memstore readbacks: "For a file source, cyclic="True" also works; Build cannot prove a cyclic memstore readback."
- The other half of item 7 is not addressed: DM316 still fires when count equals the proven producer size.

**Redaction.**
- Every reason and remediation is static. Paths are structural.
- Probes put no descriptor value and no host path in any diagnostic or on stderr:
  - row conditions: missing field, `str < int`, division by zero, over-length string, `1e999`;
  - policy refusals: step library and entry library.
- Captured values appear only in `evidence[].rows`, as on the base.

**Over-engineering.** None worth cutting.

### Findings (not P1; follow-ups)

**Info: the role-pair remediation is imprecise.** It says "remove the extra ... and add the missing one". When one identifier has two foreign keys, nothing is missing.

**Deferred: item 9 for the entry.** An `<execute>` refusal in the entry still names no element.

**Open: item 7, second half.** DM316 still fires when count equals the proven producer size.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review, and Build probes against base and head:
  - DM316 with file and cyclic sources;
  - row-condition reasons;
  - policy paths for the step and the entry;
  - a grep of every Build output for values and host paths.
- Tests: `tests_ce/unit_tests/test_authoring`, 863 passed and 4 skipped.
- ruff and mypy on the full package.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites. The coordinator reports 3,915 passed for the first head.
- CI.

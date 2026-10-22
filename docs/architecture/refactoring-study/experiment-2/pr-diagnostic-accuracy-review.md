# Diagnostic accuracy review (follow-up to #374/#378)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `fix/diagnostic-accuracy`, base `c6ff3e11` (#378 merged), head `843b06b5` (two commits).
- This review rebinds the [round 2 receipt](pr-355-373-agent-diagnostics-round-2-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source, Validation and Unknowns digests.
- **The Unknowns move is reference churn only.**
  - 14 `UNKNOWN-BOUNDARY-TYPE-POSITION` records in `datamimic_ce.engine.io.api` changed their `fact_ids` and `evidence_ids`. These are re-exports of router functions, and the `router.py` lines shifted.
  - A record-by-record diff against a fresh base collection at `c6ff3e11` shows identical ids, `data` and group membership. No reclassification is needed.
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the 313 UNKNOWN ids and the 20 diagnostics.
- **Measurements:** 1,424 unresolved calls, 178 typing positions, 255 unknown positions, 0 violations.

## Source review

**Row-condition reasons (F1, F2).**
- `_safe_number` sorts failures by cause:
  - a non-number or a bool gives TYPE_MISMATCH;
  - a number outside the budget gives OVER_BUDGET;
  - only an arithmetic result gives ARITHMETIC.
- Exact `type(...) is int/float` checks are kept on purpose, so no subclass operators run.
- An unhashable set member gives TYPE_MISMATCH.
- The unclassified fallback in `acceptance_evaluation` stays. Parse-time `ValueError`s can still reach it.

**Grammar truth.** I probed every sentence of `ROW_CONDITION_GRAMMAR` against the evaluator. All hold:
- Indexes are checked at parse time (`type(slice) in (int, str)`), so `items[-1]` and `items[True]` are rejected.
- Arithmetic is numeric only.
- The integer, float and Decimal budgets are stated as enforced. The Decimal range reads "between -128 and 128", as of 843b06b5.

**Fix in 843b06b5.** At 750220f4 the OVER_BUDGET text named no numeric budget, although out-of-range numbers now go there. The text now reads "numeric, string length, container size or nesting budget", and a test pins "numeric".

**Missing source names the step (F3).**
- `router.py` attaches `DescriptorLocation(element, attribute="source")` to `MissingSourceError` in two places: the length pass and the read.
- `DescriptorLocation` takes the current descriptor scope, so Build reports `include/<uri>/generate/source` for a step and `descriptor/<entry>/generate/source` for the entry.
- Known gap: nested-key file reads are not covered.
- Info: an `<iterate>` is reported as `generate`, the runtime statement kind. Other runtime locations behave the same way.

**Role-pair remediation (F4).**
- The branches are mutually exclusive, and none is unreachable:
  - more than one identifier;
  - no identifier, with or without FK roles naming the producer;
  - one identifier and no matching FK;
  - one identifier and two or more matching FKs.
- Each text is true for its case.
- Info: the more-than-one-identifier text assumes the consumer already has a foreign key.

**Redaction.** Every reason is static. Probes put no descriptor value and no host path in any diagnostic.

**Over-engineering.** None.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- Evaluator probes, 15 cases, at 750220f4. At 843b06b5, a re-check of the OVER_BUDGET text and the grammar's Decimal sentence.
- Build probes for a missing CSV or JSON in a step, in an `<iterate>` and in the entry.
- Tests at 750220f4: `test_authoring`, `test_portable_errors` and `test_io_files`, 941 passed and 4 skipped. At 843b06b5: `test_row_condition_reasons`, 22 passed.
- ruff and mypy at 750220f4. At 843b06b5: ruff and the format check.
- Native collection at head and at base, the UNKNOWN record diff, and the strict completion gate.

**NOT VERIFIED:**
- Full suites.
- CI.

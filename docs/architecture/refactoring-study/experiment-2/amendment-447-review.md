# Amendment 447 review: where= in the source-length key (#447)

**Approved within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/ce-file-where-columns-cache-key`, base `feat/ce-file-where-columns` (`943d7072`), head `77b36a25` (one commit).
- The amendment note under review: [amendment-447-where-length-key.md](amendment-447-where-length-key.md).
- This review rebinds the [bounded containment receipt](pr-363-bounded-containment-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Contract digest, `c70eaaf6…` → `b21806fc6b94ceb8854572ce2791cd3b373b2f9b75080906d65df2e66d9bfeb0`. The value is the `architecture_projection.contract_digest` of the gate's own ArchKeel 4.0.1 report.
- **Unchanged:** the analyzer digest, the `known-violations.json` digest, the 319 UNKNOWN identities and their group assessment, and the 20 `interface.usage_unknown` diagnostics.
- **Measurements:** 0 violations, 0 new and 0 resolved baseline entries, `calls_unresolved` 1426, `typing_positions` 182, `unknown_positions` 261.

## Contract diff (structural)

I loaded the base and head `architecture-contract.json` and compared every key and list position. There are four differences, all in `rules[6]` (`RUNTIME-API-TYPES`):

| Path | Base | Head |
|---|---|---|
| `allowed_positions[39].annotation` (`SetupContext.__init__`, `data_source_len`) | `dict[tuple[str \| None, str \| None], int] \| None` | `dict[tuple[str \| None, str \| None, str \| None], int] \| None` |
| `allowed_positions[40].annotation` (`SetupContext.data_source_len`, `return`) | `dict[tuple[str \| None, str \| None], int]` | `dict[tuple[str \| None, str \| None, str \| None], int]` |
| `provenance` length | 12 | 13 |
| `provenance[12]` | absent | `amendment-447-where-length-key.md` |

- The qualified names, positions and empty field paths are unchanged. No selector is added or removed.
- `decided_by` stays `agent`. No other rule, source, ownership, dependency, public grant, baseline or budget changes.
- The implementer's note says "exactly two selectors". That is true for selectors. The provenance append is the third, expected change.

## Source review

**The defect is real.** A same-name statement on the same file with another `where=` reused the first statement's kept-row count. The negative control below shows the lost row.

**The key is the minimal correct fix for #447.**
- `where=` exists only on `GenerateModel` (`<generate>` and its `<iterate>` alias). `VariableStatement` and `NestedKeyStatement` carry `None`, as does a `<generate>` without `where=`.
- `WhereCondition` reads only the row and the row globals, never `parent.`, variables or setup names. So for one statement name and one source, the `where=` text fully determines the kept rows. The text is a correct identity.
- `where=` with `offset=` is refused, and `where=` with a memstore, a database client or a scripted source is refused before any count. The new element cannot interact with those paths.
- Every reader of `data_source_len` goes through `data_source_cache_key` (`length.py`, `generate/task.py` twice, `variable.py`). There is one source of truth for the key.

**Alternatives checked.**
- *Encode `where=` into a string slot.* That is a string-shaped identity with collisions. Rejected, as the implementer did.
- *Key by the statement object or `id(stmt)`.* `SetupContext.__deepcopy__` deep-copies `data_source_len`, so object keys would be copied and `id()` values are not stable across copies or processes. It also changes the contract. Not simpler.
- *Skip the early return for `where=` statements.* That recounts the file for every parent record and depends on the write happening just before each read. It needs changes in the readers. Not simpler.
- *A second cache.* More state and a second key rule. Not simpler.
- No contract-neutral fix exists that keeps a typed identity. Every change of the key type changes the two pinned annotations.

**IO does not read the key.** `CountSourceRequest.source_id` keeps its two-element type, and no module under `datamimic_ce/engine/io` reads it. The runtime now passes `(stmt.full_name, stmt.source)` there explicitly.

**Redaction.** No new diagnostic text.

## Evidence

**LOCAL VERIFIED (by this reviewer):**
- The structural contract diff above.
- `make architecture-check` before the record: only "Independent review does not match the current Target and analyzer." (exit 2).
- The gate's own `check_completion` with only `contract_digest` rebound: passes with 319 assessed records. Validation failures 0, UNKNOWN identities and diagnostics identical to the review.
- Negative control: with `where` dropped from the key, `test_statements_on_one_file_with_other_conditions_keep_their_own_rows` fails with `['3', '5', '1', '2']`. With the head key it passes with `['3', '5', '1', '2', '4']`.
- `pytest tests_ce/unit_tests tests_ce/integration_tests/test_file_filter`: 3742 passed, 15 skipped.
- `mypy datamimic_ce`: no issues in 534 files. `ruff check datamimic_ce`: clean.
- `make architecture-check` after the record: exit 0, 0 violations, 319 assessed UNKNOWN records.

**NOT VERIFIED (by this reviewer):**
- Integration and functional suites other than `test_file_filter`, external-service suites, CI, Windows, EE parity, merge and release.

## Limits (not established, none blocks this amendment)

- The key is the minimal fix for #447, not a complete statement identity. Same-name statements on one source still share a count when they differ only in a database `selector`, `offset` (without `where=`), `type`, `source_entity` or `separator`. This is pre-existing, the amendment does not widen it, and Build refuses duplicate product names.
- `where=` texts that differ only in whitespace get separate keys. The cost is one extra count, not a wrong result.
- `CountSourceRequest.source_id` has no reader. Deleting the field is a follow-up outside this amendment.
- Out of scope, not checked: the dry-run row-count probe (`dryrun.py`, `_source_row_count`) builds `CountSourceRequest` without `where=`.
- The amendment note still says "Decision: open". This review records the decision; the note is listed in the contract provenance, so it stays unchanged here.

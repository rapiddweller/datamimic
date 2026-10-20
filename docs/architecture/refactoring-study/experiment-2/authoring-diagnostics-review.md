# CE Authoring diagnostics architecture review (PR #353)

**Accepted within the local architecture review scope.** The EE merge dependency is now satisfied.

- Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).
- Scope: PR #353 on `fix/authoring-diagnostics`, merged onto development. Base is `51a5be1c` (development, including #336, #346, #348, #349 and #352). Head is `c9912f5f`: merge `f415f52e`, receipt commit `907b1fca`, and the one-function follow-up `c9912f5f`.
- This review rebinds the development receipt ([issue 351 CLI review](issue-351-cli-review.md)). It keeps all of that receipt's assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source (`datamimic_ce/**/*.py`) | `5eb43dd2ddd91ca98e554e90b5adaeea464c04305268ee3d922d948ecb36523f` |
| Target, unchanged from development | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer, unchanged (ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation digest | `4db484ef6b4e01011633158d811c097cd5436cfc3266a466d07e3215838dece8` |
| UNKNOWN digest | `e1e65532fbab2833c2938d047cb0e57b04b787b086aa9b90dd0bb04296e72c14` |

The budgets are unchanged from development: 1,431 unresolved calls and 178 typing positions. This PR does not change policy, contract, baseline, gate or `measurement_amendment`.

## Merge result

The merge is textually clean. Both deltas arrive verbatim:
- `diff(51a5be1c, f415f52e)` equals the PR delta `diff(8f89cd4d, 1366cfe5)`.
- `diff(1366cfe5, f415f52e)` equals the development delta.
- Line numbers and index lines are ignored in both comparisons.
- Only the receipt conflicted. Development's receipt was taken verbatim as the starting point.

`dryrun.py` is the only product file changed on both sides. I also checked the other areas that interact semantically.

**XML includes (#346).** `neutralize_for_dry_run` is now also the `included_statement_transformer`. As a result, dynamic counts in validated XML includes also get `bounded_count_limit` and the I800 guard. I probed this:
- An included `count="{int(smalln)}"` with `smalln=3` gives a `complete` capture with 3 rows.
- An included count of 987654 is refused with I800.
- No value is echoed in either case.
- The I800 path names the entry descriptor, not the included file. This follows the existing location convention. Finding: Info.

**Policy refusals (#352/#346).** Bounded policy refusals now project `message.message`, which comes only from static `_BoundedPolicyRefusal` texts. The I800 and count paths have a catalog definition and still project title, path and guidance.

**Presenter.** It no longer uses `exclude_none`. This PR's `actual`/remediation updates are plain fields, so there is no conflict.

**Counts, generate task, acceptance and CLI input.** Development did not touch these.

The merged focused suites pass: 367 tests, 11 skipped. They cover:
- bounded executor, Build verification, `cli_v4`, dryrun and dryrun includes;
- dynamic count, diagnostic precision, key range, dryrun bounds and acceptance;
- runtime counts and the generate task;
- the redaction tests.

## EE dependency: CE issue codes must stay a subset of EE

The PR adds `IssueCode.TASK_COUNT_ABOVE_BOUNDED_LIMIT = "I800"` (`datamimic_ce/errors/codes.py:54`).

- **EE MR !431 is merged.** EE `origin/development` `3e7456a90` merges `81d43ef8e`, the rebased form of `5d19c968`.
- **Same code in both editions.** The EE catalog entry for I800 has the same name, value, title, template, cause and resolution as CE.
- **Subset holds.** Compared against EE `origin/development`, every CE `IssueCode` and `ErrorCode` at `c9912f5f` is present. `DomainErrorCode` is CE-only and is out of scope for this rule.
- **MR pipeline.** Pipeline 38149 first failed on two 90 s timeouts in EE's external banking include-properties tests. It now reports success after the replay the author describes. I checked the status only, not the cause of the timeouts.

The dependency is satisfied and recorded in the receipt's `delivery_boundary`.

## Source review of the PR delta

### Key range constraints

`KEY_RANGE_CONSTRAINTS` (`engine/dsl/model/constraints/facts.py`) has 11 facts. They match what `key_variable_task._range_generator` consumes:

- `min`/`max` need `type` int, float or decimal.
- `granularity` needs `type` float or decimal, plus `min` or `max`.
- `type=` must be the only value source. The forbidden set is derived from `KEY_GENERATION_REQUIRED`.

`KeyModel` enforces the facts, so lint, Build and `run` all reject the same forms.

### Runtime count guard

Dryrun sets `GenerateStatement.bounded_count_limit` only for a dynamic count without `source=`. A count over a source keeps the replacement count, because the source may end first.

`GenerateTask._bounded` refuses a count above the limit with I800 and never truncates. It covers both the plain path and the time-series path.

A run that completes yields a `COMPLETE` capture with `requested=None`. The rows stay bounded by `max_count × parent rows × multiplier`. A normal `datamimic run` never sets the limit.

Placement: an engine statement now carries a bounded-execution field. This follows the existing pattern in which dryrun mutates statements. The property pair matches the class style (`num_process`, the separator setters from #346). Finding: Info.

### Redaction

Bounded failures project only title, structural path and catalog guidance. The evaluated count is never projected.

Sentinel probes showed no secret value echoed in dry-run or compile output (stdout and stderr). The probes used:
- I800 with a count taken from a property file;
- `count` values `int(secretword)`, `parent.secretn`, `this.nope`, `1/0` and an unknown name;
- DM JSON with an invalid kind, a wrong-typed seed and constraint violations.

The other output paths also add no value text:
- The DateTimeGenerator reason names only the argument and the layout.
- CLI file errors show only the basename.
- The capture message reuses the already published `evidence.reason`.

### Findings

**Low, resolved in `1366cfe5`.** After `e1307d79`, the count-scope hint was chosen from the location alone, so non-name failures also got it. `_runtime_hint` now also requires a `NameError` or `AttributeError` cause. I re-probed after worker transport:
- `parent.secretn`, an unknown name and `this.nope` get the count-scope hint.
- `int(secretword)` and `1/0` get the catalog resolution.

**Info.** The I800 path does not name the product. That is acceptable under the conservative redaction policy.

**P2 follow-up, accepted (`c9912f5f`).** `_incomplete_capture_remediation` (`authoring/domain/acceptance_evaluation.py:505-513`) used to give every UNKNOWN capture the same advice: use a literal count or a finite source.
- That advice does not resolve two UNKNOWN causes: unresolved memstore producer bindings and an incomplete parent capture.
- UNKNOWN captures now point to their named capture reason. That reason is already in the message and is value-free.
- CAPPED advice is unchanged. CAPPED arises in two places:
  - `cap_applied` with observed rows equal to the limit (`dryrun.py:1150`). Causes: a static count or range above `max_count`, a file source above it, a dynamic count over a source, and DB, Mongo, memstore or scripted sources.
  - Memstore availability above the limit (`dryrun.py:1238`).
- For each of these, a static bound or a finite source within `max_count` does make completeness provable. So the advice is correct.
- An explicit count up to the authoring maximum still gets the more specific "increase max_count" retry advice.
- Info: the CAPPED advice does not also mention raising `max_count` for file or memstore sources. That would be an alternative fix; the current advice is not wrong.
- The new test `test_unknown_capture_names_its_reason_without_prescribing_a_cardinality_fix` passes; the acceptance module passes 66/66.

No finding blocks acceptance.

## Native result and UNKNOWN assessment

Fresh `make architecture-check` at `f415f52e`, and again at `c9912f5f`, failed only on the stale receipt:
- 534/534 files covered; `failures` is empty.
- 0 violations, 0 baseline additions or resolutions.
- Rules are 271 PASS and 5 UNKNOWN.
- Validate exits 2 with the same 20 `interface.usage_unknown` diagnostics as development. The full report exits 0.

I re-collected development `51a5be1c` independently. It reproduces every digest of development's receipt. At `c9912f5f` only the source digest changed. The validation and UNKNOWN digests, the calls and the 314 records are identical to `f415f52e`.

**Calls against development:**

| | Development | Head |
|---|---|---|
| Total | 13,010 | 13,053 |
| Resolved | 9,578 | 9,621 |
| Unresolved | 1,431 | 1,431 |
| Partially resolved | 2,001 | 2,001 |

With comprehension line numbers ignored, the only difference among the unresolved and partially resolved calls is `logical_path.as_posix`. It moved from `CeDescriptorValidator.validate` into the extracted `_rule_diagnostics`. No call was added semantically or promoted.

**UNKNOWN records: 311 → 314.**
- Added: the three `GenerateStatement.bounded_count_limit` positions (`reason: inherited_surface`). They join `inherited_surface`, which grows from 136 to 139.
- Removed: none.
- Changed content: 12 records keep their IDs.
  - 11 changed only fact or evidence references after line shifts.
  - The DSL-API-TYPES summary now counts 392 positions.

No record is dropped or reclassified as PASS.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Merge-delta equivalence.
- Semantic review of the overlap areas, including an include probe.
- EE code sets and catalog text at EE `origin/development` `3e7456a90` (after the merge).
- MR !431 merge state and pipeline status.
- Native collection at head and at development.
- Decoded call and UNKNOWN diffs.
- Redaction probes.
- 367 merged focused tests.
- Strict completion gate acceptance of 314 assessed UNKNOWNs.
- ruff and full mypy (534 files) on `f415f52e` and `c9912f5f`.

**NOT VERIFIED:**
- Full unit and integration suites. The author reports 3,056 passed and 15 skipped; I did not rerun them.
- CE CI for `c9912f5f`. A green CI run was reported for `907b1fca`; I did not check it.
- The cause of the original !431 banking timeouts.
- EE runtime parity (datamimic-ee#69).
- External services and Windows.

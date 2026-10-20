# CE Authoring diagnostics architecture review (PR #353)

**Accepted within the local architecture review scope, with one merge dependency.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex). Scope: `8f89cd4d..1366cfe5` on `fix/authoring-diagnostics`. This replaces the source binding of the [Authoring and Errors final review](authoring-errors-final-review.md). It does not authorize a merge and does not assert native all-PASS.

## Current binding

- Source: `d0639ab7bb276a2cc914ee6189efb01567c3031c38643046818cd108955a6840` (scope `datamimic_ce/**/*.py`).
- Target: `8517a10b1fd874b2e66f7161044074d8ff649639a9f8e37e17f92c2456cc0d85` (unchanged).
- Analyzer: `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` (unchanged). ArchKeel 4.0.1, Python 3.11.12.
- Canonical validation digest: `58f46fe03fa319561e98b351eef61f64d49eeb713963f089862ea64e6d73ef18`.
- UNKNOWN digest: `69312f5ce17a36d8c2be8867448da9a5e129f1873ac7800102c321978195b344`.
- Budgets are still exactly 1,425 unresolved calls and 178 typing positions. This change does not amend policy, contract, baseline or gate.

## Merge dependency: CE issue codes must stay a subset of EE

The change adds `IssueCode.TASK_COUNT_ABOVE_BOUNDED_LIMIT = "I800"` (`datamimic_ce/errors/codes.py:54`).

- At base `8f89cd4d`, every CE `IssueCode` and `ErrorCode` existed in EE with the same name and value.
- EE `origin/development` (`a3f1a3718`) has no I800, and neither does any other EE ref. So at HEAD the subset holds only together with EE MR !431.
- EE MR !431 is branch `fix/reserve-bounded-count-issue-code` at `5d19c968`. It registers the same name and value and the same catalog title, template, cause and resolution. Against that commit, every CE `IssueCode` and `ErrorCode` is present in EE.
- `DomainErrorCode` is CE-only. It was already outside EE at base and is out of scope for this rule.
- When this review was written, MR !431 was still open and pipeline 38149 was still running.

**CE #353 must not merge before MR !431.** This dependency is recorded in the receipt's `delivery_boundary`.

## Source review

### Key range constraints

`KEY_RANGE_CONSTRAINTS` (`engine/dsl/model/constraints/facts.py:378-406`) contains 11 declarative facts. They match what `key_variable_task._range_generator` (lines 209-219) actually consumes:

- `min`/`max` need `type` int, float or decimal.
- `granularity` needs `type` float or decimal, plus `min` or `max`.
- `type=` must be the only value source. The forbidden set is derived from `KEY_GENERATION_REQUIRED`, so there is no second list.

`KeyModel` (`key_model.py:313-316`) enforces the facts, so lint, Build and `run` all reject the same forms. Other attributes are unaffected: `<variable>` does not use the range path, and string/binary length attributes are separate.

### Runtime count guard

Dryrun sets `GenerateStatement.bounded_count_limit` only for a dynamic count without `source=` (`authoring/adapters/dryrun.py:468-478`). A dynamic count over a source still uses the replaced count, because the source may run out first.

`GenerateTask._bounded` (`engine/runtime/tasks/generate/task.py:104-114`) refuses a count above the limit with I800 and never truncates. It applies to both the plain path and the time-series series-count path. Time series keeps the existing per-invocation semantics, the same as a static count.

Capture evidence for the guarded case:
- A run that completes is `COMPLETE` with `requested=None`.
- The existing `max_count × parent rows × multiplier` validation still bounds the captured rows.
- Normal `datamimic run` never sets the limit.

Placement: an engine statement now carries a bounded-execution field. This follows the existing pattern in which dryrun mutates statements (count, targets, num_process). The property pair also matches the class style, for example `num_process`. Finding: Info.

### Redaction

CE diagnostics stay free of descriptor values. Bounded failures project only title, structural path and catalog guidance (`bounded_executor.py:176-215`). The evaluated count in the I800 template is never projected.

Sentinel probes (`authoring dry-run` and `compile`, stdout and stderr) echoed no secret value from a property-file value or from the DM JSON input:
- I800 with a count taken from a property file;
- `int(secretword)`, `parent.secretn`, `this.nope`, `1/0` and an unknown name in `count`;
- DM JSON with an invalid kind, a wrong-typed seed and constraint violations.

The other redaction paths also add no value text:
- The DateTimeGenerator reason names only the argument and the layout. It stays a `ValueError` subclass.
- CLI file errors echo only the basename.
- The capture message reuses `evidence.reason`, which Build evidence already publishes.
- The lint fallback reruns static rules on parser failure, which is the same input the linter already accepts.

The three named regression tests pass.

### Findings

- **Low, resolved in `1366cfe5`:** after `e1307d79` located every count failure at `generate/count`, `dryrun.py` chose `GUIDANCE_COUNT_SCOPE` from the location alone, so `int('text')` and `1/0` received name-scope advice. `_runtime_hint` (`dryrun.py:158-165`) now also requires a `NameError`/`AttributeError` cause and otherwise returns the catalog resolution. Re-probed after worker transport: `parent.secretn`, an unknown name and `this.nope` get the count-scope hint; `int(secretword)` and `1/0` get "Fix the expression or script and retry."; no value is echoed.
- **Info:** the I800 path does not name the product. That is acceptable under the conservative redaction policy for product names.

No blocking source finding.

## Native result and UNKNOWN assessment

Fresh `make architecture-check` fails only with "Validation changed after independent review." The rest of the result:
- Coverage 534/534 full AST.
- 0 violations, 0 baseline additions or resolutions.
- Rules still 271 PASS and 5 UNKNOWN.
- Exit 2 with the exact 20 `interface.usage_unknown` diagnostics, identical to the previous receipt.

The base was independently re-collected from a `8f89cd4d` snapshot and reproduces every previous receipt digest.

Calls went from 12,958 to 13,001; resolved went from 9,539 to 9,582. Decoded comparison of the unresolved (1,425) and partially resolved (1,994) calls shows only relocations: three line shifts and the `_rule_diagnostics` extraction. No call was added semantically or promoted.

UNKNOWN records went from 303 to 306:
- **Added (3):** the getter return, setter value and setter return positions of `GenerateStatement.bounded_count_limit` (`DSL-API-TYPES`, `reason: inherited_surface`). They join the `inherited_surface` group, which grows from 130 to 133.
- **Removed:** none.
- **Changed content, same ID (12):**
  - 11 `GenerateStatement` positions changed fact and evidence IDs only, after line shifts.
  - The `DSL-API-TYPES` summary now counts 388 positions (inherited_surface 46, undecided 73).

No record is dropped or reclassified as PASS, and none is used to justify removing a public entry.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of the delta.
- EE code-set comparison at base, at HEAD and at MR !431.
- Native collection at HEAD and base.
- Decoded call and UNKNOWN diffs.
- Redaction sentinel probes.
- ruff passes; full mypy is clean (534 files) at `1366cfe5`.
- Focused suites: 234 passed with 11 skipped, then 146 passed with 11 skipped at both `e1307d79` and `1366cfe5`.
- Strict completion gate acceptance of 306 assessed UNKNOWNs.

**NOT VERIFIED:**
- Full unit and integration suites.
- CE CI.
- The MR !431 pipeline result and merge.
- EE runtime parity (datamimic-ee#69).
- External database delivery.

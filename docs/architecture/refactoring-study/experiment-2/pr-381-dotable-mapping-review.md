# DotableDict mapping protocol review (PR #381, #355 item 11)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/dotable-mapping`, base `a7059fa8` (origin/development), head `42977a85` (three commits).
- This review rebinds the [diagnostic accuracy receipt](pr-diagnostic-accuracy-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests. Validation moves through coverage counts (13,409 calls analysed) and through `typing_positions` 178 → 182.
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the Unknowns digest, the 313 UNKNOWN records and the 20 diagnostics.
- **Measurements:** 1,424 unresolved calls, 255 unknown positions, 0 violations.

### Budget raise: `typing_positions` 178 → 182

**Authorization.** The owner's standing explicit acceptance of 2026-10-22: "das archkeel budget darf immmer erhoeht werden wenn es verargumentierbar und geprueft ist ... bitte so merken".
- It is recorded in the owner's memory as `feedback_archkeel_budget_may_be_raised.md`.
- The condition it sets: the raise is argued, measured, and the baseline equals exactly the measured value.

**Verification against the native typing signals.** Exactly four positions are new, and each is `object`:
- `DotableDict.__getitem__` return;
- `DotableDict.get` default;
- `_plain` value;
- `_plain` return.

`get`'s return was already `object` on the base. `object` is the honest type for heterogeneous row values. The baseline is the measured 182, and no other budget moved.

## Source review

**The protocol.**
- `DotableDict` gains `__getitem__`, `__iter__`, `__len__`, `__contains__`, `get(key, default=None)` and `keys()`.
- It is registered as a virtual `Mapping`, not a subclass, so the `items()`/`values()` methods cannot shadow row fields with those names.
- Errors are mapped as before:
  - `row['missing']` gets the static "KeyError: missing mapping key";
  - `row.missing` raises AttributeError (chained from the KeyError) and gets `_SCOPE_GUIDANCE`, without echoing the name.
- `DotableDict` is created only in `context.py` and in `variable/task.py`, and results leave through `_plain`. So no engine code depends on the old behaviour where `get` raised for a missing key, and none relies on a row's truthiness.

**Result export: blocked at f82a83da, fixed in 42977a85.**
- At f82a83da, `_plain` rebuilt every dict and list result. That broke identity with a stored dict, turned `defaultdict`, `Counter` and `OrderedDict` into plain `dict` (a `defaultdict` variable then raised KeyError on a missing key), and made a whole stored lookup dict cost O(size) per row.
- Now only exact dicts and lists are rebuilt, and a dict with no row in it keeps its identity.
- A base-vs-head probe confirms identity and the subclass types, and that `dict(row)`, `{'r': row}` and `[row]` export as plain dicts.
- A new test fails without the fix.

**Low (ceiling).** A script that returns a whole large container still walks it, O(size) per evaluation: about 90 ms for a 200k-entry dict. The base already copied lists shallowly. Skipping the walk for a `DotableDict` would make that case O(1), but `script="this"` could then leak a variable's source row, since those rows are stored as `DotableDict`s inside the scope dict.

**Redaction.** No new diagnostic text, and no row values appear.

**Over-engineering.** None. Each protocol method serves `dict(row)`, `in` or iteration.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- The evaluator probe against base and head.
- The native typing-signal inspection.
- Targeted tests: 25 passed (the protocol unit tests, expression evaluation, and the DSL functional test).
- ruff.
- Native collection and the strict completion gate.

**NOT VERIFIED (by this reviewer):**
- Full suites. The coordinator reports them passing, apart from the known SQLite xdist flake.
- mypy at this head.
- CI.

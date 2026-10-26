# Seeded load-time entropy warning review (PR #390, #359)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/seeded-entropy-warning`, base `cbecf0a6` (#384 merged), head `598ad6a8` (two commits).
- This review rebinds the [#384 receipt](pr-384-log-line-breaks-review.md) and keeps all of its assessments.
- **Merge precondition:** EE MR !463 reserves W008. CE issue codes stay a subset of EE's, so this PR must not merge before !463 has merged.
- It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests. Validation moves through coverage counts only (13,501 calls analysed).
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the Unknowns digest, the 313 UNKNOWN records and the 20 diagnostics.
- **Measurements:** 1,424 unresolved calls, 182 typing positions, 255 unknown positions, 0 violations.

## Review

**The change.** `ExecuteTask._eval_python` statically scans every inline or uri Python script under `<setup rngSeed>`. It emits W008 `EXECUTE_SEEDED_LOAD_TIME_ENTROPY` once per script and line:
- for a draw at load time: module level, a default argument, a decorator, or a class body;
- for an entropy import inside a function or class body that draws from that module.

The warning only logs: `datamimic run` still exits 0, and Build outcomes are unchanged. Build's forced replay of seeded models that load Python stays the hard check; a load-time `random.randint` is rejected there.

**Blocked at d74a5d9f, then fixed:**
- **B1:** W008 did not exist in EE. EE MR !463 now reserves it, with catalog text identical to CE's.
- **B2:** the resolution claimed a seeded stand-in that `time` and `secrets` do not have. The scan now covers only names that are rebound to a seeded stand-in: `random.*`, `uuid1`/`uuid4`, `datetime` `now`/`utcnow`/`today`, and `os.urandom`. The resolution text says so.

**False positives removed** (re-probed):
- `random.Random(<arg>)` and `random.seed(<arg>)`;
- `time.perf_counter`;
- an import inside a body that does not draw, such as `timedelta`, `uuid.UUID` or `time.sleep`;
- `os.path`.

True positives are kept:
- `Random()`, `SystemRandom()`;
- a default `now()`, `date.today()`;
- class-body and module-level draws;
- `uuid4`/`now` drawn after a body import.

**Redaction.** The warning carries the script basename, the line and a static draw text.

### Findings (not P1)

**Low: the resolution text over-promises for some name imports.**
- The stand-in covers `random` as a module, and the listed members when they are imported by name.
- An unlisted member imported by name is not covered, for example `from random import triangular`. The scan flags such a draw, yet moving it into a function does not seed it.
- Probe: two seeded runs give different `triangular()` values and the same `randint()` values.
- The gap is in `rebind_seeded_script_names` and predates this PR. The fix belongs there: rebind every public `random` function. Track it separately.

**Accepted heuristic gaps.** The scan misses `__name__` guards, aliasing, `from random import *`, `getattr`/`__import__` and numpy.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- The EE MR diff: catalog text byte-identical to CE's. The MR is open.
- A 24-case scan probe.
- A seeded determinism probe for name-imported `random` members.
- Build and run probes at d74a5d9f.
- `test_load_time_entropy` and the DSL functional test: 30 passed.
- ruff.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites, and mypy at this head. The coordinator reports both clean.
- EE CI for !463.
- CI.

## Addendum: `3d33533b` and `652a9d7d` (Codex P2 threads)

**Accepted at `652a9d7d`.**

What `3d33533b` changed:
- The seed exemption now needs a seed value that is not the constant `None`, given positionally or as the `x`/`a` keyword. `Random(None)`, `Random(x=None)`, `seed(None)` and `seed(version=2)` are flagged again.
- Eager function annotations are scanned, including those of `async def`, unless the module uses `from __future__ import annotations`.
- For a generator expression, only the outermost iterable is scanned.

**Blocked at 3d33533b.** Scanning only the outermost iterable missed generators that a call consumes while the module loads. Example:
- `TOKEN = ''.join(random.choice(...) for _ in range(12))` was flagged at 598ad6a8 but not at 3d33533b.
- Two seeded runs produced different tokens and no W008.

**Fixed in 652a9d7d.** A `GeneratorExp` passed directly as a call argument is scanned whole: its element, every iterable and every `if`. A stored generator keeps the outer-iterable-only rule.

**Re-probed at 652a9d7d:**
- **Flagged:** `join`, `list`, `sum`, `tuple`, `set`, `any`, `all`, `max`, `min`, `sorted` and `next` over a drawing generator; a drawing `if`; a nested consumed generator; a method-call argument; a generator inside a keyword-argument call.
- **Not flagged:** a stored generator, its nested inner iterable, and a function body.
- **Real run:** the two-run `TOKEN` case now logs W008 at line 3. The values still differ, as expected for a warning.

**Accepted edges:**
- A non-constant seed (`Random(seed_var)`) or `Random(*args)` counts as seeded.
- Module-level variable annotations are scanned even when annotations are postponed.

**Binding.** The Source and Validation digests move, Validation through coverage counts only (13,517 calls analysed). Contract, Unknowns, the 313 UNKNOWN records and the 20 diagnostics are unchanged, and so are the 1,424 / 182 / 255 measurements. EE !463 is still the merge precondition; the catalog text did not change.

**LOCAL VERIFIED:**
- A 27-case probe at 3d33533b and a 20-case generator probe at 652a9d7d.
- The two-run determinism probe.
- `test_load_time_entropy` and the DSL functional test: 44 passed.
- ruff.
- Native collection and the strict completion gate.

## Addendum: rebased onto `96aa455e` (head `73747da9`)

- **The patch is unchanged.** Diffed against its base, it is line for line the same as the reviewed `652a9d7d` diffed against `cbecf0a6`.
- **The merge precondition is met.** EE MR !463 is merged, and `W008 EXECUTE_SEEDED_LOAD_TIME_ENTROPY` is on EE `origin/development`.
- **Binding:**
  - Source and Validation move.
  - Unknowns, Contract, analyzer and the 20 diagnostics are unchanged.
  - Measurements are 1,428 / 182 / 261.
- **LOCAL VERIFIED:**
  - `test_load_time_entropy` and the DSL functional test: 44 passed.
  - Native collection and the strict completion gate.

## Addendum: `c1e4472c` (four Codex findings)

**Accepted.** EE MR !464 carries the corrected W008 text and must merge before #390.

**Annotations are no longer scanned.**
- Verified by experiment: a seeded script with `def f(x: random.random()) -> random.random()` returns `{'x': 'random.random()', 'return': 'random.random()'}` from `f.__annotations__`, and no W008 is logged.
- `exec` inherits `from __future__ import annotations` from `engine/runtime/scripting/plugins/__init__.py`, so annotations stay strings.
- That inheritance is the reason this rule is true. Info: if the module ever drops the future import, annotations would be evaluated again.

**Generators.** Only a generator handed to a known eager consumer is scanned whole. The consumers are `join`, `list`, `tuple`, `set`, `frozenset`, `dict`, `sum`, `min`, `max`, `any`, `all`, `sorted` and `next`; probed, all are flagged. Not flagged:
- `iter(...)`, `map(...)` and a stored generator: correct, since they are consumed later, inside seeded code.
- `S.update(...)`: a method consumer. This is an accepted heuristic gap.

**Import bindings follow scopes.**
- A function-local import no longer binds the module scope.
- A module-level draw through the expression namespace's seeded `random`, with no import, is correctly not flagged.

**Resolution text.**
- In seeded functions, `os.urandom` and `uuid1` are `_Uncontrolled` stand-ins that refuse to draw. They have no seeded replacement, so the new text ("use random.randbytes or uuid4 instead") is true.
- The text is byte-identical to EE MR !464 (open).

**Binding.** Source and Validation move. Unknowns, Contract and the 20 diagnostics are unchanged, as are the 1,428 / 182 / 261 measurements.

**LOCAL VERIFIED:**
- A 29-case scan probe.
- The annotation experiment.
- The EE MR diff.
- `test_load_time_entropy` and the DSL functional test.
- ruff.
- Native collection and the strict completion gate.

## Addendum: squashed onto `c648a0a9` (head `960dd1b0`)

- **The patch is unchanged.** Against `c648a0a9` it is line for line the same as the reviewed `c1e4472c` against `96aa455e`. This covers `datamimic_ce`, `tests_ce` and `docs/migrations`.
- **Merge precondition.** EE MR !464 (the corrected W008 text) must merge before #390.
- **Binding:**
  - Source and Validation move.
  - Unknowns, Contract, analyzer and the 20 diagnostics are unchanged, and so are the 1,428 / 182 / 261 measurements.
  - The rebind uses a gate run that finished without a collector error.

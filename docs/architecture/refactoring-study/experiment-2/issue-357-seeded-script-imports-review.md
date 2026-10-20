# Seeded script imports architecture review (issue 357, PR #358)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `fix/seeded-script-imports`, base `aa0fbb3a`, head `a257e98e` (`c4bd5fe3`, `8d07520a`, `aa6714b8`, `a257e98e`).
- This review rebinds the [PR #353 receipt](authoring-diagnostics-review.md). It keeps all of that receipt's assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `055823b58e8e061972137aef6d88df471bc68e80a7099825aea33d41b0aafd9d` |
| Target (unchanged) | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `1425294602da4a7cbc5a58740602a9f64d0c79f4f2b3be645c994438c7889e4e` |
| UNKNOWN | `3fba47d636af0ba444f171245ea70846adfe4704739f1b7fed82c216de731d62` |

Budgets are unchanged: 1,431 unresolved calls and 178 typing positions. No policy, contract, baseline, gate or `measurement_amendment` change.

## What changed

```
<execute> script runs in initial_ns (context.py:457)
  └─ seeded run? rebind_seeded_script_names (expression_globals.py:270)
       ├─ identity rebind: random, uuid, datetime, np, pd, os modules,
       │  datetime.datetime/date, uuid.uuid4 -> seeded _EvalProxy stand-ins
       │  random.Random -> SeededRandom (real Random subclass, :285)
       └─ random/uuid/datetime/pd/np/os stay private (:308-320, context.py:466);
          aliases (rnd, Datetime, Random) are exported as before
expression evaluation: expression_globals (:248) builds the same seeded globals as before
```

## Source review

**The original issue is fixed.** At base `aa0fbb3a`, a script's `import random` changed more than the helper's own draws:
- The raw module was exported and shadowed the seeded expression global.
- That broke replay for `values=`, `fake`, `uuid` and `random` columns elsewhere in the model.

At head, helpers draw from the setup rng:
- Seeded fixtures replay identically across fresh processes. The unseeded fixture differs between runs.
- A mixed model (helpers plus DSL `random`/`datetime`/`fake`/generator keys) gives exactly the same non-helper columns as the same model without the script.

**No change for models that do not import these names.** I compared seeded output at base and head and it was identical for:
- a model with no `<execute>`;
- a model whose script imports nothing;
- a model whose script imports only `os` and `json`.

`expression_globals` returns the same objects as before.

**Findings from my earlier rounds are resolved:**
- `isinstance` checks now delegate to the real class through `_EvalProxy.__instancecheck__` and `__subclasscheck__` (`:123-128`). A helper's `isinstance(x, datetime)` / `isinstance(x, date)` returns True/True again (False/False at `c4bd5fe3`).
- `Random` is a real subclass, so `isinstance` and subclassing work.
- Aliases are shared again. These work and replay under seed:
  - `Datetime(2020, 1, 2)`;
  - `rnd.randint` in an expression;
  - a second script using `rnd` from the first.
- `_EvalProxy.__deepcopy__` (`:130`) returns the shared proxy. The `generator=`-key namespace copy (`context.py:95` → `_deepcopy_namespace`) therefore no longer crashes. I re-probed:
  - `from datetime import datetime` + `generator=` under seed: it previously failed with RecursionError; it now runs and replays.
  - `import random as rnd` + `generator=` under seed: it previously failed with the `random.SystemRandom` entropy error; it now runs and replays.
  - The shipped demo-datetime script with a `generator=` key, seeded: runs and replays.
- The new fixture keys cover the deep-copy path.
- `SeededRandom` is now built only once per script rebind. `seeded_random` and `SeededRandom` share one seeding rule, `_random_seed` (`:165`).
  - Performance: base 2.9–3.3 s, `c4bd5fe3` 2.9–3.3 s, head 3.0–3.4 s for 20,000 rows × 5 seeded `script=` keys. That is within noise; the 3× per-expression cost measured at `aa6714b8` is gone.

**Other copy paths.** Context serialization through `dill` (`generate_worker.py:49`) runs only for `num_workers > 1` (`task.py:266`). Seeded runs force single-process execution. A seeded model with `numProcess="2"`, aliases and `generator=` replays.

**Redaction.** No new user-facing message path. `_Uncontrolled` refusals stay static texts.

### Findings

- **Info: type annotation.** The `_EvalProxy` target annotation `ModuleType | type | RandomSource` keeps typing positions at 178. It truthfully describes every call site: the rng, the uuid, datetime, pandas, numpy and os modules, and the datetime, date and Timestamp classes. It is a real narrowing, not a suppression.
- **Info: shadowing.** A script `from datetime import datetime` still shadows the `datetime` module in later expressions. This is the same seeded and unseeded, and the same as base (`datetime.datetime.now()` → AttributeError). It is not introduced by this PR.
- **Info: members imported by name.** These, such as `from random import randint`, stay raw. This is documented in the docstring.
- **Info: proxy state.** `__getattr__` has no guard for missing instance state. Only `deepcopy` reaches it today, and `deepcopy` is now short-circuited.

No blocking finding.

## Native result and UNKNOWN assessment

Fresh `make architecture-check` failed only on the stale receipt:
- 534/534 files covered; `failures` is empty.
- 0 violations, 0 baseline additions or resolutions.
- Rules are 271 PASS and 5 UNKNOWN.
- Validate exits 2 with the same 20 `interface.usage_unknown` diagnostics. The full report exits 0.

I re-collected base `aa0fbb3a` independently. It reproduces every digest of the previous receipt.

**Calls:** 13,053 → 13,069; resolved 9,621 → 9,636; unresolved 1,431 → 1,431; partially resolved 2,001 → 2,002.

With comprehension line numbers ignored, the call differences are:
- The two anchored-clock `anchor.replace` calls moved from `expression_globals.now` to `_seeded_objects.now`.
- `rng.getrandbits` moved into `_random_seed`.
- One partially resolved call was added: `namespace.items` in `rebind_seeded_script_names`, an annotated receiver.

No call was promoted.

**UNKNOWN records:** 314 → 314 with identical IDs.
- 58 `SetupContext` boundary positions changed only fact and evidence references, after line shifts in `context.py`.
- No title or data changed.
- Every record keeps its previous group.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of `aa0fbb3a..a257e98e`.
- Fresh-process replay and probes at base, `c4bd5fe3`, `aa6714b8` and head.
- Performance measurements.
- Native collection at head and base.
- Decoded call and UNKNOWN diffs.
- ruff and full mypy (534 files).
- Determinism scenarios: 20 passed.
- Context, clock, Faker, expression-globals, memstore API, runtime boundary and generate-task tests: 211 passed, 11 skipped.
- Strict completion gate acceptance.

**NOT VERIFIED:**
- Full unit and integration suites. The author reports five `-n auto` failures that pass serially; I did not reproduce them.
- CE CI.
- External services and Windows.
- EE parity.

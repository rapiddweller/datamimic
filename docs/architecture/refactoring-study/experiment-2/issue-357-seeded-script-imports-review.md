# Seeded script imports architecture review (issue 357, PR #358)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `fix/seeded-script-imports`, base `aa0fbb3a`, head `8c6ce49e`. The PR is part of #357.
- Commits reviewed: `c4bd5fe3`, `8d07520a`, `aa6714b8`, `a257e98e`, `490501bc`, `3465825f`, `8c6ce49e`.
- This review rebinds the [PR #353 receipt](authoring-diagnostics-review.md). It keeps all of that receipt's assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `b57d660e73b64cf9980943c3aa0017b70af584bf23e50858ccadda0f60453051` |
| Target (unchanged) | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `63f5480fee09892367d09080cb0d0cbf828039319f9a5e2cacfd1ebfd470d917` |
| UNKNOWN | `3fba47d636af0ba444f171245ea70846adfe4704739f1b7fed82c216de731d62` |

Budgets are unchanged: 1,431 unresolved calls and 178 typing positions. No policy, contract, baseline, gate or `measurement_amendment` change.

## What changed

```
<execute> script runs in initial_ns (context.py:457)
  └─ seeded run? rebind_seeded_script_names (expression_globals.py:283)
       ├─ identity rebind (:311-338): random, uuid, datetime, np, pd, os modules;
       │  datetime.datetime/date, uuid.uuid4; members imported by name
       │  (random.random/randint/.../seed/SystemRandom, uuid.uuid1, os.urandom)
       │  -> seeded _EvalProxy stand-ins and their members
       │  random.Random and random-module .Random -> one SeededRandom class (:302)
       ├─ random.seed(x) with a value -> refusal (:191); seed()/seed(None) -> no-op
       ├─ Random() and Random(None) -> seed drawn from the run (_random_seed, :160)
       └─ random/uuid/datetime/pd/np/os stay private (:343-356, context.py:466);
          aliases (rnd, Datetime, Random) are exported as before
expression evaluation: expression_globals (:261) builds the same seeded globals as before,
  except that random.Random(None) now draws from the run like random.Random()
```

## Source review

### Original issue fixed

At base `aa0fbb3a`, a script's `import random` changed more than the helper's own draws:
- The raw module was exported and shadowed the seeded expression global.
- That broke replay for `values=`, `fake`, `uuid` and `random` columns elsewhere in the model.

At head, helpers draw from the setup rng:
- Seeded fixtures replay identically across fresh processes. The unseeded fixture differs between runs.
- A mixed model (helpers plus DSL `random`/`datetime`/`fake`/generator keys) gives exactly the same non-helper columns as the same model without the script.

### Expressions and unseeded runs unchanged

- Unseeded runs never call the rebind.
- `expression_globals` passes `functools.partial(_seeded_random, rng)` and `_ignore_seed`, so expression behaviour is as before.
- Seeded output is byte-identical at base and head for:
  - a model with no `<execute>`;
  - a model whose script imports nothing;
  - a model whose script imports only `os` and `json`;
  - expressions `random.Random(5).random()`, `random.Random().random()` and `random.randint`.

### Earlier findings resolved

- **Type checks.** `isinstance`/`issubclass` delegate to the real class (`:123-128`). Seeded helper checks for `datetime`, `date` and both `Random` spellings return True.
- **Aliases.** Aliases and names shared across scripts are exported and replay.
- **Deep copies.** `__deepcopy__` returns the shared proxy (`:130`). The `generator=`-key namespace copy therefore keeps one stream. I re-probed under seed:
  - `from datetime import datetime` + `generator=`: runs and replays;
  - `import random as rnd` + `generator=`: runs and replays;
  - the shipped demo-datetime script: runs and replays;
  - a `numProcess="2"` variant: runs and replays.
- **Other copy paths.** `dill` context serialization runs only for `num_workers > 1`, and seeded runs force single-process execution.
- **Per-expression cost.** `SeededRandom` is built once per script rebind, not per expression. End-to-end time for 20,000 rows × 5 seeded `script=` keys is within noise of base.
- **Keyed `random.seed`.**
  - Before: a keyed `random.seed(k)` was silently ignored, so values no longer depended on the key. At base, every row of `keyed(1)` was 140892.
  - Now: `seed(x)` with a value raises a static refusal in both the module and by-name forms. The message recommends `random.Random(x)` and echoes no value.
  - `seed()` and `seed(None)` remain no-ops in scripts, because they would otherwise draw OS entropy.
  - Expressions keep the existing no-op.
  - The new fixture pins the refusal.
- **Docstring.** It now accurately states that body-time draws, imports inside helper bodies and unlisted members are not seeded, and that neither a plain run nor Build detects them.
  - I confirmed that a module-level `X = random.randint(...)` differs between two seeded runs.
  - Build rejects a descriptor with `<execute>` as `unsupported_bounded_operation`, with replay `blocked` (open issue #332).

### `Random(None)` (`8c6ce49e`)

The Codex P2 finding is valid. `Random(None)` seeds from OS entropy exactly like `Random()`, but the seeded override passed `None` through to the stdlib constructor. `_random_seed` (`:160`) now draws 64 bits from the run for both forms. The sentinel class is removed, so there is one rule for expressions, `SeededRandom` and the `seed` refusal. `_refuse_keyed_seed` behaves as before.

Probes:
- **Expressions.** At base, `random.Random(None).random()` differed between runs. At head it replays, and it equals `random.Random().random()`.
- **Stream shift.** The one extra draw shifts later `random.*` columns in such models. This is the intended, accepted move toward determinism. It no longer mirrors EE; the author tracks that on datamimic-ee#73.
- **Unchanged models.** Models that do not call `Random(None)` are byte-identical to base: no script, a plain script, an `os`-only script, and `Random(5)`/`Random()`/`randint` expressions.
- **Earlier probes.** The deepcopy, alias, `isinstance`, demo-datetime, `numProcess=2` and keyed-seed refusal probes still pass. The fixtures replay across fresh processes, including `helper_own_random` with `Random(None)`. The unseeded fixture differs between runs.

### Redaction

No value is echoed. I checked a property-derived key passed to the refused `seed` in a bounded `authoring run --allow-side-effects`: stdout and stderr contained no value.

### Findings

- **Info: remediation text.** In bounded authoring runs, the seed refusal is shown with the generic scope-hint remediation, because the projection shows the issue title, not the refusal text. Build refuses `<execute>` anyway; this affects only `authoring run --allow-side-effects`.
- **Info: type annotation.** The `_EvalProxy` target annotation `ModuleType | type | RandomSource` truthfully narrows `object` and keeps typing positions at 178.
- **Info: shadowing.** A script `from datetime import datetime` still shadows the `datetime` module in later expressions. This is the same seeded and unseeded, and the same as base.
- **Low, pre-existing, not blocking: reseeding an instance.** Calling `seed()` or `seed(None)` on an existing Random instance still draws OS entropy. Example: `r = Random(5); r.seed()` in a seeded script differed between two runs, and it did so at base too.
  - One-method fix: override `seed` on `SeededRandom` to pass the value through `_random_seed`.
  - Expression-side `Random` instances behave the same way.
  - The receipt's `delivery_boundary` records this.
- **Deferred by the user (CE follow-up issue).** Draws while the script body executes, and imports inside helper bodies. These are pre-existing and are documented in the docstring and `delivery_boundary`.

No blocking finding.

## Native result and UNKNOWN assessment

Fresh `make architecture-check` failed only on the stale receipt:
- 534/534 files covered; `failures` is empty.
- 0 violations, 0 baseline additions or resolutions.
- Rules are 271 PASS and 5 UNKNOWN.
- Validate exits 2 with the same 20 `interface.usage_unknown` diagnostics. The full report exits 0.

My earlier re-collection of base `aa0fbb3a` reproduces the previous receipt's digests.

**Calls against base:** 13,053 → 13,069; resolved 9,621 → 9,636; unresolved 1,431 → 1,431; partially resolved 2,001 → 2,002.

With comprehension line numbers ignored, the call differences are:
- The two anchored-clock calls moved into `_seeded_objects.now`.
- `rng.getrandbits` moved into `_random_seed`.
- One partially resolved call was added: `namespace.items` in `rebind_seeded_script_names`.

No call was promoted.

**UNKNOWN records:** 314, with identities identical to base. The UNKNOWN digest is unchanged since `a257e98e`. Compared with base, 58 `SetupContext` positions changed only fact and evidence references. No title or data changed, and every record keeps its group.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of `aa0fbb3a..8c6ce49e`.
- Fresh-process replay, refusal, redaction and regression probes.
- Native collection and decoded diffs.
- ruff and full mypy (534 files).
- Determinism scenarios, contexts, clock, Faker, memstore API, runtime boundary, generate task and the `extensive_script` integration suites: 237 passed, 11 skipped (at `3465825f` and again at `8c6ce49e`).
- Strict completion gate acceptance.

**NOT VERIFIED:**
- Full unit and integration suites. The author reports `-n auto` flakes that pass serially; I did not reproduce them.
- CE CI.
- External services and Windows.
- EE parity.

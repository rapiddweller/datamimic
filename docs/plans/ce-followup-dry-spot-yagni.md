# Multi-Agent Plan — CE DRY / SPOT / YAGNI Follow-ups

**Branch:** `refactor/ce-followup-dry-spot-yagni` (based on `feat/ce-determinism-full-contract`)
**Origin:** the pre-existing items surfaced by the 5-agent review on PR #132 that were
intentionally left out of that PR's scope. This plan cleans them up *separately*.
**Executor for every workstream:** model `sonnet`, agent type `python-pro`.

> These are **behaviour-preserving refactors and dead-code removals**. No generated
> output may change. The seeded-replay model `tests_ce/integration_tests/test_determinism_dsl/all_entities_seeded.xml`
> must stay **byte-identical** after every workstream (regenerate and `git diff` it).

---

## 0. Ground rules (apply to all agents)

1. **No behaviour change.** Same seed → same output. After your change:
   - regenerate the determinism model and confirm it is unchanged:
     `uv run python tests_ce/integration_tests/test_determinism_dsl/test_determinism_dsl.py && git diff --exit-code tests_ce/integration_tests/test_determinism_dsl/all_entities_seeded.xml`
   - run the gates: `uv run pytest -q tests_ce/architecture/ tests_ce/integration_tests/test_determinism_dsl/`
2. **Trust but verify dead code.** Before deleting any symbol, prove zero callers with
   `git grep -n "<symbol>" -- datamimic_ce tests_ce` (and check for dynamic/string lookups).
   Quote the grep result in your summary.
3. **Lint + types must stay clean:** `uv run ruff check <changed files>` and `uv run mypy datamimic_ce`
   (the only allowed pre-existing mypy errors are the two optional `ray` import-not-found lines).
4. **Scope discipline.** Touch only the files listed for your workstream. If you find an
   adjacent issue, note it in your report — do **not** expand the diff.
5. **One commit per workstream**, message prefix as specified. Report `file:line` for every change.
6. **TDD where it adds a guarantee** (Workstream B): add the failing test first, then the fix.

### File-ownership matrix (guarantees zero merge conflicts → all 5 run in parallel)

| Workstream | Owns (exclusive) |
|---|---|
| A — Services | `domain_core/base_domain_service.py` + the **23** `domains/**/services/*_service.py` |
| B — Weighted pick | `domains/utils/dataset_loader.py` + the generators that do anti-repeat picking (list below) |
| C — order_generator | `domains/ecommerce/generators/order_generator.py` only |
| D — Dead code (util) | `domains/common/literal_generators/generator_util.py` only |
| E — Transaction to_dict | `domains/finance/models/transaction.py` only |

No file appears in two rows ⇒ the five agents may be launched concurrently.

---

## Workstream A — Collapse `supported_datasets()` boilerplate (DRY + consistency)

**Agent:** `python-pro` (sonnet) · **Commit:** `refactor(services): lift supported_datasets() into BaseDomainService`

**Problem.** All **23** services repeat an identical `supported_datasets()` staticmethod;
only the `patterns` list differs. Evidence: `git grep -l "def supported_datasets" -- 'datamimic_ce/domains/**/services/*.py'` → 23 hits. Representative (`common/services/person_service.py`):
```python
@staticmethod
def supported_datasets() -> set[str]:
    from pathlib import Path
    from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets
    patterns = ["common/person/givenName_male_{CC}.csv", ...]
    return compute_supported_datasets(patterns, start=Path(__file__))
```

**Task.**
1. In `base_domain_service.py` add a class attribute `DATASET_PATTERNS: tuple[str, ...] = ()`
   and a single concrete `classmethod supported_datasets()` that resolves patterns relative to
   the **subclass's own file**:
   `compute_supported_datasets(cls.DATASET_PATTERNS, start=Path(inspect.getfile(cls)))`.
   ⚠️ Must use `inspect.getfile(cls)` (subclass module), **not** `Path(__file__)` of the base,
   or dataset discovery resolves against the wrong directory.
2. In each of the 23 services, replace the staticmethod with a class attribute
   `DATASET_PATTERNS = (...)` holding exactly the existing pattern strings. Delete the now-dead
   per-file imports of `Path` / `compute_supported_datasets`.
3. **Consistency nits** (same files, fold in here to avoid a second pass over 23 files):
   - use keyword `dataset=` everywhere (fix positional `OrderGenerator(dataset, ...)` in
     `order_service.py`, `BankGenerator(dataset, ...)` in `bank_service.py`);
   - standardise on `from random import Random` (drop `import random` / `random.Random`);
   - standardise the `reference_now` annotation on one alias (`datetime`, not `dt.datetime`).

**Acceptance.**
- `supported_datasets()` returns the **same set** for every entity before/after — verify with a
  quick script that imports each service class and compares to a snapshot taken before the change.
- Determinism model byte-identical; `tests_ce/architecture/` + `tests_ce/api_tests/` green.
- No `def supported_datasets` remains in any `*_service.py`.

---

## Workstream B — One weighted-pick-without-repeat helper (DRY + latent-bug fix)

**Agent:** `python-pro` (sonnet) · **Commit:** `fix(generators): unify weighted pick-without-repeat; guarantee non-repetition`

**Problem.** The "load weighted CSV, pick one, avoid immediate repeat" idiom is reimplemented
several different ways. Two **single-retry** variants do **not** guarantee non-repetition (a
re-draw can return the same value):
- `healthcare/generators/patient_generator.py` `pick_blood_type` (single retry)
- `public_sector/generators/police_officer_generator.py` `get_department`, `pick_unit` (single retry)

Correct filter-pool variants (to be unified, not "fixed"):
- `finance/generators/bank_account_generator.py` (account type, currency)
- `finance/generators/bank_generator.py`
- `common/generators/city_generator.py` (`_last_state`), `common/generators/company_generator.py` (`_last_legal_form`)
- `insurance/generators/insurance_policy_generator.py` (`pick_status`)
- `healthcare/generators/doctor_generator.py`, `healthcare/generators/medical_device_generator.py`

**Task (TDD).**
1. In `domains/utils/dataset_loader.py` add
   `pick_one_weighted_no_repeat(rng, values, weights, *, last) -> str` next to the existing
   `pick_one_weighted` / `sample_weighted_no_replacement`. Semantics: pick by weight from the
   pool **excluding** `last` when more than one distinct value exists (filter-and-renormalise —
   guarantees non-repetition); fall back to the full pool when only one value.
2. **First** write unit tests in `tests_ce/unit_tests/` proving: (a) never repeats `last` when
   ≥2 distinct values; (b) deterministic for a fixed `rng`; (c) returns the sole value when only one.
3. Refactor every site above to call the helper. Track each generator's `_last_*` field exactly
   as today.
4. While here, remove the dead `load_weighted_values` (the non-`_try_dataset` variant) from
   `dataset_loader.py` — verify zero callers first (`git grep -n "load_weighted_values\b" | grep -v _try_dataset`).

**⚠️ Behaviour note.** Fixing the two single-retry variants to *guarantee* non-repetition **may
change generated values** for those two fields. That is the intended correctness fix, but it means
the determinism model's affected entities (PoliceOfficer, Patient) will produce new — still
deterministic — values. If the committed `all_entities_seeded.xml` changes only for those entities'
relevant keys, **regenerate and commit it** and call this out explicitly in the PR. All other
entities must stay byte-identical.

**Acceptance.** New helper unit tests green; determinism replay test green (regenerate model if
PoliceOfficer/Patient values shifted); no `_try_dataset`-less `load_weighted_values` remains.

---

## Workstream C — De-duplicate `order_generator` CSV blocks (DRY)

**Agent:** `python-pro` (sonnet) · **Commit:** `refactor(ecommerce): extract order_generator weighted-CSV helper`

**Problem.** `domains/ecommerce/generators/order_generator.py` repeats the same
`read CSV → header.get(col) → pick_one_weighted` block ~6× (`get_order_status`,
`get_payment_method`, `get_shipping_method`, `get_currency_code`, plus `get_shipping_amount`),
re-importing `dataset_path`/`FileUtil` inside each method.

**Task.** Extract one private helper, e.g.
`def _pick_from_weighted_csv(self, *path, value_col, weight_col="weight") -> str`, and route the
methods through it. Hoist the repeated imports to module top. Keep method names/signatures and
the exact CSV columns each uses.

**Acceptance.** `order` API tests + determinism model byte-identical (Order block unchanged).

---

## Workstream D — Remove dead `GeneratorUtil` methods (YAGNI)

**Agent:** `python-pro` (sonnet) · **Commit:** `chore(generators): drop dead GeneratorUtil discovery methods`

**Problem.** `domains/common/literal_generators/generator_util.py` exposes
`get_supported_generators` and `get_all_generator_names` with **zero callers** (verified:
`git grep -n "get_supported_generators\|get_all_generator_names" -- datamimic_ce tests_ce`
returns only the definitions). `get_supported_generators` is also a hand-maintained category dict
that duplicates the auto-discovered `generator_namespace()` — exactly the manual list the
determinism PR set out to kill.

**Task.** Delete both methods and any imports/constants they alone used (re-verify with grep,
including string/dynamic references). Do **not** touch other methods in the file.

**Acceptance.** `uv run mypy datamimic_ce` + full unit suite green; grep confirms removal.

---

## Workstream E — `Transaction.to_dict()` SPOT consistency

**Agent:** `python-pro` (sonnet) · **Commit:** `refactor(finance): serialise Transaction.account via account.to_dict()`

**Problem.** `domains/finance/models/transaction.py` (~lines 230-234) serialises the nested
account as an **inline dict literal**:
```python
if self.account:
    result["account"] = {"account_number": self.account.account_number,
                          "account_type": self.account.account_type}
```
Every other model serialises nested records via `<obj>.to_dict()` (Address, Hospital, Product,
InsurancePolicy.coverages). This inline literal can drift from `BankAccount`'s real schema.

**Task.** Replace the inline literal with `result["account"] = self.account.to_dict()` (keep the
`if self.account:` guard — `account` is optional). 

**⚠️ Behaviour note.** `BankAccount.to_dict()` emits *more* keys than the two inlined here, so the
serialised `account` sub-dict will grow. This is a deliberate consistency fix but **does change
output**. Confirm the determinism model: `account` is an *optional* group and is excluded from the
seeded model (it's `None` under the seed), so `all_entities_seeded.xml` should stay byte-identical
— verify. Update any `test_transaction` assertions that pinned the old 2-key shape.

**Acceptance.** `tests_ce/api_tests/test_transaction/` green; determinism model byte-identical;
schema gate green.

---

## Sequencing & merge

- **Parallel:** A, B, C, D, E have disjoint file ownership → launch all five concurrently
  (one message, five `Agent` calls, `subagent_type: python-pro`, `model: sonnet`).
- **Caveat:** B and E may legitimately change `all_entities_seeded.xml` (PoliceOfficer/Patient
  values; account stays excluded). If two workstreams both regenerate it, reconcile by
  regenerating once at the end (Workstream A/C/D must leave it byte-identical).

## Global verification gate (run after all five land)

```bash
uv run python tests_ce/integration_tests/test_determinism_dsl/test_determinism_dsl.py
git diff --stat tests_ce/integration_tests/test_determinism_dsl/all_entities_seeded.xml   # expect: only B/E if anything
uv run ruff check datamimic_ce tests_ce
uv run mypy datamimic_ce                                                                  # only the 2 ray errors allowed
uv run pytest -q tests_ce/architecture/ tests_ce/unit_tests/ tests_ce/api_tests/ \
               tests_ce/functional_tests/ tests_ce/integration_tests/test_determinism_dsl/ \
               tests_ce/integration_tests/test_entity/
```
Expected: all green except the known environmental `external_service_tests` (need live DBs) and
`tests_ce/unit_tests/test_mcp/test_e2e.py::test_sse_transport_roundtrip` (socket).

## Out of scope (explicitly NOT in this plan)
- Multiprocessing determinism (`numProcess > 1`) — separate, larger change (per-record index-seeding).
- The remaining `import random` style nits beyond the 23 services.

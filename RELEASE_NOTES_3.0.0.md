# DATAMIMIC 3.0.0

_Release date: 2026-05-23 · Previous release: [2.2.0](https://github.com/rapiddweller/datamimic/releases/tag/2.2.0)_

DATAMIMIC 3.0.0 turns the CE determinism *promise* into a contract: **same seed + same model = byte-identical output**, locked in by architecture gates, exposed at the DSL level via a new model-wide `<setup rngSeed>`, and proven by committed full-entity scenario models. It also lands a new domain-agnostic **time-series primitive** on `<generate>`, a rebuilt three-tier generator hierarchy, and a substantial cleanup pass.

Several of the underlying changes are observable — schema types, `to_dict()` shapes, previously-silent fallbacks, the PyPI distribution name — hence the major bump.

---

## Highlights

- **Determinism, end-to-end.** Single RNG channel, single clock SPOT, frozen anchor for seeded runs, registry-driven entity discovery, and AST-level gates that forbid raw `datetime.now()` in CE prod code. (#132)
- **DSL `<setup rngSeed>`.** A model-wide seed at the root of `<setup>`; per-block `<variable rngSeed>` overrides; no seed anywhere → wall-clock random. Consistent attribute name across all levels. (#134)
- **Deterministic `distribution="random"` source reads.** Seeded runs now replay source-order identically across CSV, `.ent.csv`, JSON, SQLite, and cascading `<nestedKey>` reads — unseeded behaviour unchanged. (#135)
- **Time-series primitive on `<generate>`.** Domain-agnostic loop modifier driven by ISO 8601 `start` / `end` / `interval`. One primitive serves IoT readings, financial ticks, log streams, smart meters. (#136)
- **CE cleanup.** DRY/SPOT/YAGNI pass across 12 generators and 23 services; silent value-fabricating fallbacks replaced with clear `ValueError`s. (#133)
- **CI on Node 24** and **PyPI distribution renamed to `datamimic`**. (#129, #130)
- **Honest README.** Compliance framing tightened, CE/EE boundary sharpened, CE-only value surfaced. (#131, #135)

---

## ⚠️ Breaking changes

### PyPI distribution renamed
The package is now published to PyPI as **`datamimic`**. Update your install:

```bash
pip install -U datamimic
```

TestPyPI auto-uploads have been removed; tags continue to publish to prod PyPI. (#130)

### Determinism contract: `rng` is the only signal
The legacy `seeded_mode` flag is gone. A generator is seeded iff an `rng` is supplied; passing `None` seeds from the wall clock. A subtle bug where `Random(0)` was treated as unseeded is fixed. If you constructed generators relying on the `seeded_mode` flag, switch to passing an explicit `Random(seed)`. (#132)

### `to_dict()` now serializes nested model objects to dicts
Previously, `to_dict()` on some models emitted raw nested model objects (e.g. `Order.shipping_address`, `Order.billing_address`, `Doctor.hospital`, `Order.product_list`, `Transaction.account`). They now serialize via the nested model's `to_dict()` — matching `InsurancePolicy.coverages` and every other model. **Downstream consumers that expected nested object references will see dicts instead.** (#132, #133)

### Schema type corrections
- `PoliceOfficer.birthdate` was declared `str` but emitted `datetime` → corrected to `datetime`.
- `InsurancePolicy` date fields were declared `datetime` but emitted `date` → corrected to `date`.

The new schema-consistency gate now catches this class of mismatch going forward. (#132)

### Silent fallbacks → `ValueError`
Several generators previously fabricated plausible-but-wrong data when source files or keys were missing. They now raise `ValueError` naming the offending file/key. Affected paths:

- `transaction_generator`: merchant, amount range, type modifier, currency symbol, description template
- `order.get_shipping_amount` (no silent `0.0`), product rating / insurance premium / coverage count, product nouns, `bank_account` currency, person salutation
- `repo_root` raises instead of silently returning `/`

Intentionally retained: the US dataset fallback in `dataset_path`, the analogous US country fallback, and `routing_number=""` for locales without a US-style routing concept. (#133)

### Removed APIs (dead code)
- `EntitySchema.field_names`
- `GeneratorUtil.faker_generator`, `GeneratorUtil.get_supported_generators`, `GeneratorUtil.get_all_generator_names`
- Registry: `describe_entity`, `list_entity_names`, `service_path`
- `attribute_catalog.spec_to_dict`
- Generator `get_generator_class`
- `BaseDomainService` override hooks
- `is_strict_dataset_mode` pass-through wrapper
- Speculative `reference_now` parameter on address fields

### DSL attribute name normalized
The model-wide seed attribute is `<setup rngSeed>` (not `<setup seed>`). The attribute name is consistent at every level: `<setup rngSeed>`, `<variable rngSeed>`, `<demographics rngSeed>`. (#134)

---

## ✨ New features

### `<setup rngSeed>` — model-wide DSL seed (#134)
A single seed at the root of `<setup>` propagates a reproducible child RNG to every seed-less `<variable entity="...">` in the model. Per-block `<variable rngSeed="...">` overrides it. No seed anywhere keeps the wall-clock random behaviour.

Three committed full-model DSL scenarios pin the contract (every entity + a representative scalar of every attribute and sub-structure):

| Model | Seeding | Contract |
|---|---|---|
| `seed_in_setup.xml` | `<setup rngSeed>` only | two runs byte-identical |
| `seed_setup_and_generator.xml` | setup + per-variable `rngSeed` | variable seed overrides setup; seed-less follows setup |
| `no_seed.xml` | none | two runs differ |

Models are generated by a shared builder and sync-checked — a new entity can't skip the gate.

### Deterministic `distribution="random"` source reads (#135)
`distribution="random"` shuffles a source. Previously the shuffle seed came from the per-run task id, so a *seeded* run still read the source in a different order every time — silently breaking reproducibility (e.g. source-based pseudonymization).

`get_distribution_seed()` now derives the shuffle seed from the run's root RNG when `<setup rngSeed>` is set, so `distribution="random"` replays identically. Without a setup seed, the per-run behaviour is preserved (privacy-maximized default). Proven across:

| Source | seeded → reproducible | unseeded → random |
|---|---|---|
| plain `.csv` | ✅ | ✅ |
| `.ent.csv` | ✅ | ✅ |
| `.json` | ✅ | ✅ |
| SQLite (`<database dbms="sqlite">` + `<execute>` + `selector`) | ✅ | ✅ |
| cascading generates (`<nestedKey source=… distribution="random">`) | ✅ | ✅ |

Deterministic shuffling across distributed / multi-process execution remains the EE differentiator.

### Generic time-series primitive on `<generate>` (#136)
ISO 8601 `start` / `end` / `interval` attributes turn any `<generate>` into a time-series loop. Per iteration the script context exposes a `ts` namespace (`ts.now`, `ts.step`, `ts.series`). Output column names, value formulas, and whether to emit an ID column at all are entirely user-controlled.

```xml
<generate name="ticks" count="3"
          start="2026-01-01T09:30:00Z"
          end="2026-01-01T10:00:00Z"
          interval="PT5M"
          target="ticks.csv">
  <key name="timestamp" script="ts.now.isoformat()"/>
  <key name="symbol"    script="['AAPL','MSFT','GOOG'][ts.series]"/>
  <key name="price"     script="100 + ts.step * 0.25"/>
</generate>
```

One primitive serves IoT readings, financial ticks, log streams, smart meters — without per-domain code.

### Three-tier generator hierarchy (#132)
`BaseDomainGenerator` (RNG) → `DatasetAwareDomainGenerator` (normalized dataset) → `ClockAnchoredDomainGenerator` (frozen clock). The clock-anchored layer pins "now" once per entity so all date-derived fields are mutually consistent. All domain + literal generators migrated.

### EE-style entity + generator registries (#132)
Auto-discovery resolves entities by name; no more hand-maintained lists. Inconsistent `dataset="US"` defaults centralized in `normalize_dataset`.

### Typed `EntitySchema` / `FieldSpec` (#132)
Fields are declared by their real Python type; the JSON type string is *derived*, never duplicated.

---

## 🛠 Improvements & refactors

- **SPOT for child-RNG derivation** (`runtime/derive_child_seed`): the `Random(parent.randrange(2**63))` idiom was duplicated in three places (generator, setup root, demographics) — now one helper, reused by `spawn_rng` and `get_distribution_seed`. (#133, #134, #135)
- **SPOT for `supported_datasets()`**: lifted from 23 services into one `BaseDomainService` classmethod driven by a `DATASET_PATTERNS` class attribute. (#133)
- **Unified weighted-pick "avoid repeat" idiom** into one `dataset_loader.pick_one_weighted_no_repeat` (filter-and-renormalise — *guarantees* non-repetition). Fixes single-retry variants that could still repeat. Applied across 5 domains / 12 generators. (#133)
- **Headered-CSV weighted pick** moved to its proper layer (`dataset_loader.pick_weighted_from_headered_csv`); `order_generator` now delegates. (#133)
- **`ATTR_RNG_SEED` constant** replaces 7 brittle `"rngSeed"` string literals. (#134)
- **Shared DSL model builder** (`tests_ce/integration_tests/dsl_model_builder.py`): one parameterised function describes the complete model, reused by sync-checks and all determinism scenarios. (#134)
- **`administration_office`**: model no longer mutates generator private state — staff count moves into the generator (de-duplicating ranges); hours-signature dedup via a generator property. (#133)
- **`StringGenerator`** threads RNG through the `exrex` regex sampler (extracted as a context-managed seam). (#132)
- **Faker** seeded via `seed_instance(...)` instead of a global/unseeded instance. (#132)
- **Set-ordering leak fix**: `educational_institution_generator` used `list(set(...))` of strings → `PYTHONHASHSEED`-dependent selection; fixed to order-stable `dict.fromkeys`. (#132)

## 🔒 Architecture gates (lock-in tests)

These run in CI and prevent silent regressions:

- **Clock-drift gate** — AST-walks CE prod code, forbids raw `datetime.now()`.
- **Schema-consistency gate** — `emitted_keys ⊆ declared`, and declared types match runtime types.
- **Service-replay**, **facade determinism**, and **DSL replay** gates at their respective layers.
- **Determinism DSL sync-check** — `all_entities_seeded.xml` is regenerated from the registry and compared byte-for-byte; new entities can't skip the gate.

## 🐛 Bug fixes

- `Random(0)` was treated as unseeded by the old `seeded_mode` flag. (#132)
- `Transaction.to_dict()` now serialises `account` via `account.to_dict()` (matches every other model). (#133)
- `Transaction.account` correctly marked `optional=True` (it's `BankAccount | None`). (#132)
- VN datasets conformed to the parser contract (numeric `premium_buckets_VN`, `Generic`/`Điều chỉnh` row in `description_templates_VN`, `Giáo dục` merchants in `merchants_VN`) — these were silently producing garbage before. (#133)

## 📦 Build & CI

- **Node 24** for all GitHub Actions (#129)
- **PyPI distribution renamed to `datamimic`** (#130)
- **TestPyPI auto-upload removed.** Tags still publish to prod PyPI via the `release` job. (#130)
- Makefile and `datamimic_ce/mcp/cli.py` adjustments alongside the Actions upgrade. (#129)

## 📚 Documentation

- **Compliance framing tightened**: dropped "compliance layer" wording for GDPR/HIPAA/PCI in favour of "audit evidence support". DATAMIMIC produces evidence; it does not provide a regulatory safe harbor. Added SWIFT CSP caveat next to EDIFACT/SWIFT MT (test/training only). (#131)
- **CE vs EE clarity**: "Supported systems" table reworked into explicit CE/EE columns; Oracle, MS SQL, MySQL, SQLite correctly marked CE. EE-only bullets in the "What is DATAMIMIC" list marked explicitly. (#131)
- **"Where CE fits on its own"** — three concrete standalone use cases (CI/CD, MCP for AI agents, pseudonymization). CE domains table expanded from 3 to 6 (Healthcare, Finance, Insurance, E-commerce, Public sector, Demographics). CLI reference expanded from 3 to 8 verified commands. (#131)
- **"Where DATAMIMIC fits in your compliance program"** table maps deterministic outputs to EU AI Act Art. 10/50, DORA Art. 8/24-27, ISO 27701:2025 A.1.4/A.1.2.9, HIPAA §164.312, and GDPR Art. 25 — with a legal disclaimer. (#131)
- **Pseudonymization example is runnable.** Previously used converters that don't exist (`anonymize_email`, `generate_iban`, `shift_date`) and invalid `<key>` attributes — rewritten to the working pattern (seeded `<variable entity=...>` overwrites each PII field). Real converters listed (`Mask`, `Hash`, `MiddleMask`, `CutLength`, `DateFormat`). (#135)
- **`distribution="ordered"`** documented as required for reproducible source-based pseudonymization. (#135)
- **Determinism section reworked**: documents the CE DSL seed hierarchy and honestly lists the runtime SPOTs (the previous claim referenced `resolve_rng`, which never existed). (#134)
- **`CLAUDE.md`** project guidelines added: no lint fixes in `tests_ce/**`; DSL models stay checked in (+ sync-check). (#134)

---

## Known gaps (intentionally out of scope)

- **Multiprocessing determinism** (`numProcess > 1`) still re-seeds each worker from the same base seed without an index offset — single-process determinism only in CE. Cross-process deterministic shuffling remains the EE differentiator.
- Other-locale data is incomplete: `categories_{FR,GB,ES}.csv` and `product_nouns_*_VN.csv` are missing, and `administration_office` DE parses a phone string as float. These predate 3.0.0 and are surfaced (not introduced) by the new clear errors in #133.

---

## Verification

- `ruff` clean (prod)
- `mypy` clean (pre-existing optional `ray` import only)
- ~1350 in-process tests green
- Determinism DSL models byte-identical across repeated runs
- Only failing tests are environment-bound `external_service_tests` (need live DBs) and one MCP socket test — unrelated

## Upgrade checklist

- [ ] Update install to `pip install -U datamimic` (distribution rename).
- [ ] Audit any code that consumed `to_dict()` on `Order`, `Doctor`, `Transaction`, `PoliceOfficer`, or `InsurancePolicy` — nested-object fields are now dicts; some date/datetime types are corrected.
- [ ] Replace any reliance on the removed dead APIs (see Breaking changes).
- [ ] Replace any reliance on silent fallbacks in `transaction_generator`, `order.get_shipping_amount`, product rating / insurance premium / coverage count, product nouns, `bank_account` currency, person salutation, or `repo_root` — these now raise `ValueError`.
- [ ] If you set `seed` at the `<setup>` root, rename to `rngSeed` (consistent across `<setup>`, `<variable>`, `<demographics>`).
- [ ] For reproducible source-based pseudonymization, set `<setup rngSeed>` and use `distribution="ordered"` (or `distribution="random"` now that it honours the setup seed).

---

## Full commit log (last 4 weeks on `development`)

| Commit | Date | PR | Summary |
|---|---|---|---|
| `abbf034` | 2026-05-23 | [#136](https://github.com/rapiddweller/datamimic/pull/136) | Generic time-series primitive on `<generate>` |
| `665b463` | 2026-05-22 | [#135](https://github.com/rapiddweller/datamimic/pull/135) | README critical review + deterministic random source reads (CE) |
| `da591db` | 2026-05-22 | [#134](https://github.com/rapiddweller/datamimic/pull/134) | feat(dsl): model-wide `<setup rngSeed>` + DSL determinism scenarios |
| `b9238e7` | 2026-05-22 | [#133](https://github.com/rapiddweller/datamimic/pull/133) | refactor: CE follow-up — DRY / SPOT / YAGNI cleanup + clearer control flow |
| `f6e77e0` | 2026-05-21 | [#132](https://github.com/rapiddweller/datamimic/pull/132) | feat: CE determinism full contract |
| `e97e12e` | 2026-05-19 | [#131](https://github.com/rapiddweller/datamimic/pull/131) | docs: tighten compliance claims, expand CE value, sharpen CE/EE separation |
| `3ffaf2c` | 2026-05-18 | [#130](https://github.com/rapiddweller/datamimic/pull/130) | ci: rename PyPI distribution to `datamimic` and fix TestPyPI publish |
| `5cafb56` | 2026-05-18 | [#129](https://github.com/rapiddweller/datamimic/pull/129) | ci: upgrade actions to Node 24 |

**Full diff:** [`2.2.0...3.0.0`](https://github.com/rapiddweller/datamimic/compare/2.2.0...3.0.0)

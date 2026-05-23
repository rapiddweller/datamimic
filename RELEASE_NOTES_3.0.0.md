# DATAMIMIC 3.0.0

_Release date: 2026-05-23 · Previous release: [2.2.0](https://github.com/rapiddweller/datamimic/releases/tag/2.2.0) · 8 PRs (#129–#136)_

Three themes:

1. **Determinism is now a contract, not a promise.** Same seed + same model = byte-identical output, locked in by architecture gates.
2. **Time-series generation as a first-class DSL primitive** — domain-agnostic, deterministic-by-construction, prefix-stable.
3. **CE cleanup** — DRY/SPOT/YAGNI pass, silent fallbacks turned into clear errors.

---

## ✨ Time-series generation on `<generate>` (#136)

A `<generate>` becomes a time-series loop the moment you add ISO 8601 `start` / `end` / `interval`. Per iteration the script context exposes a `ts` namespace:

| Variable | Type | Meaning |
|---|---|---|
| `ts.now` | `datetime` | current tick |
| `ts.step` | `int` | position within one series (`0..N-1`) |
| `ts.series` | `int` | which series this row belongs to (`0..count-1`) |

```xml
<generate name="ticks" count="3"
          start="2026-01-01T09:30:00Z" end="2026-01-01T10:00:00Z" interval="PT5M"
          target="ticks.csv">
  <key name="timestamp" script="ts.now.isoformat()"/>
  <key name="symbol"    script="['AAPL','MSFT','GOOG'][ts.series]"/>
  <key name="price"     script="100 + ts.step * 0.25"/>
</generate>
```

**Design guarantees:**

- **Prefix-stable by construction** — the first N ticks of series 0 are byte-identical regardless of total window length (each `ts.now` is a pure function of `start + interval * step`).
- **Contiguous loop order per series** — series 0 in full, then series 1, etc. Trivial downstream grouping.
- **Pagination-invariant** — `pageSize` cannot perturb output.
- **`count` is orthogonal** — still means outer-loop iterations; total rows = `count × ticks_per_series`. Default `count="1"` keeps single-series fixtures terse.
- **Strict ISO 8601** — `PT1H`, `PT15M`, `PT0.001S` (1 ms), `PT0.000001S` (1 µs floor), `P1D`, `P1W`. Months/years and sub-µs intervals rejected with a clear error.
- **Helpful error messages** — every parse error names the offending attribute, echoes the bad value, and shows a canonical example (e.g. `interval="1h"` → error suggests `PT1H`).
- **Composes** with `<key condition>`, `<nestedKey>`, and `<variable source="…">` — the `ts` namespace is visible wherever a script runs. `<variable name="ts">` is rejected at parse time to prevent shadowing.

One primitive serves IoT readings, financial ticks, log streams, smart meters — no per-domain code. Proven by 15 committed DSL fixtures + 18 tests in `tests_ce/integration_tests/test_timeseries/`.

---

## 🔒 Determinism contract (#132, #134, #135)

| | What changed |
|---|---|
| **Single signal** | A generator is seeded iff an `rng` is supplied; `None` → wall-clock. The old `seeded_mode` flag and a `Random(0)`-treated-as-unseeded bug are gone. |
| **Clock SPOT** | `runtime/clock.now_utc_naive()` is the only sanctioned wall-clock read; seeded runs use a frozen `DETERMINISTIC_ANCHOR`. AST gate forbids raw `datetime.now()` in CE prod code. |
| **Generator hierarchy** | `BaseDomainGenerator` (RNG) → `DatasetAwareDomainGenerator` (normalized dataset) → `ClockAnchoredDomainGenerator` (frozen clock, anchored once per entity so all date fields stay mutually consistent). |
| **Schema as SoT** | Typed `EntitySchema` / `FieldSpec` — JSON type string is *derived*, not duplicated. Schema-consistency gate checks `emitted ⊆ declared` and that types match runtime. |
| **DSL** | New `<setup rngSeed>` propagates a reproducible child RNG to every seed-less `<variable entity="…">`; `<variable rngSeed>` overrides; consistent attribute name at every level. |
| **Source reads** | `distribution="random"` now derives its shuffle seed from `<setup rngSeed>`, so seeded runs replay source order identically across CSV, `.ent.csv`, JSON, SQLite, and cascading `<nestedKey>`. Unseeded behaviour unchanged. |
| **Gates** | Clock-drift, schema-consistency, service-replay, facade-determinism, DSL-replay, and a sync-checked `all_entities_seeded.xml` generated from the registry — new entities can't skip. |

Three committed full-model DSL scenarios pin the contract (`seed_in_setup.xml`, `seed_setup_and_generator.xml`, `no_seed.xml`).

---

## 🛠 CE cleanup (#133)

- **SPOT**: `supported_datasets()` lifted from 23 services into `BaseDomainService`; `pick_one_weighted_no_repeat` (filter-and-renormalise — *guarantees* non-repetition) replaces 5 divergent implementations, two of which could still repeat.
- **Silent fabrications → `ValueError`** naming the offending file/key: `transaction_generator` (merchant, amount range, type modifier, currency symbol, description template), `order.get_shipping_amount`, product rating / insurance premium / coverage count, product nouns, `bank_account` currency, person salutation, `repo_root`.
- **`to_dict()`** now serializes nested model objects as dicts (matching `InsurancePolicy.coverages` and every other model): `Order.shipping_address`, `Order.billing_address`, `Order.product_list`, `Doctor.hospital`, `Transaction.account`.
- **VN datasets** conformed to the parser contract — these were silently producing garbage before.
- **Dead API removed**: `EntitySchema.field_names`, `GeneratorUtil.faker_generator` / `get_supported_generators` / `get_all_generator_names`, registry `describe_entity` / `list_entity_names` / `service_path`, `attribute_catalog.spec_to_dict`, generator `get_generator_class`, `BaseDomainService` override hooks, `is_strict_dataset_mode` wrapper.

---

## ⚠️ Breaking changes (upgrade in this order)

1. **`<setup seed>` → `<setup rngSeed>`** (and per-block `<variable rngSeed>`, `<demographics rngSeed>`).
2. **Schema types corrected**: `PoliceOfficer.birthdate` → `datetime` (was `str`); `InsurancePolicy` date fields → `date` (were `datetime`).
3. **`to_dict()` shape**: previously-nested model objects are now dicts (see #133 list above).
4. **Silent fallbacks now raise `ValueError`** (see #133 list above). US dataset / country fallbacks and empty `routing_number` for non-US locales are intentionally retained.
5. **Removed dead APIs** (see #133 list above).
6. **Determinism plumbing**: if you constructed generators relying on `seeded_mode`, pass an explicit `rng=Random(seed)` instead. `Random(0)` is now correctly seeded.

---

## 📦 Build, CI, docs

- **GitHub Actions on Node 24** (#129) — Makefile and `datamimic_ce/mcp/cli.py` adjustments alongside.
- **TestPyPI auto-uploads removed** (#130) — tags still publish to prod PyPI via the `release` job. (The package's PyPI distribution name was changed in the same PR; that change was unintentional and is not a deliberate part of this release.)
- **README** (#131, #135): compliance framing tightened ("audit evidence support" not "compliance layer"), SWIFT CSP caveat, EE-only bullets marked, CE/EE columns added to "Supported systems", CE domains 3 → 6, CLI reference 3 → 8 verified commands, pseudonymization example is now runnable, determinism section honest about the real runtime SPOTs.

---

## Known gaps (out of scope)

- **Multiprocessing determinism** (`numProcess > 1`) still re-seeds each worker from the same base seed without an index offset — CE remains single-process-deterministic; cross-process is the EE differentiator.
- Other-locale data incomplete: `categories_{FR,GB,ES}.csv`, `product_nouns_*_VN.csv`, `administration_office` DE phone field. Predate 3.0.0; surfaced by the new clear errors in #133.

## Verification

`ruff` clean · `mypy` clean (pre-existing optional `ray` aside) · ~1350 in-process tests green · determinism DSL models byte-identical · time-series prefix-stable and pagination-invariant. Only failing tests are environment-bound `external_service_tests` and one MCP socket test — unrelated.

---

**Commits:** `5cafb56` · `3ffaf2c` · `e97e12e` · `f6e77e0` · `b9238e7` · `da591db` · `665b463` · `abbf034`
**Full diff:** [`2.2.0...3.0.0`](https://github.com/rapiddweller/datamimic/compare/2.2.0...3.0.0)

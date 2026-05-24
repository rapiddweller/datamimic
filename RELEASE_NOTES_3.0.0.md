# DATAMIMIC 3.0.0

_Release date: 2026-05-23 · Previous release: [2.2.0](https://github.com/rapiddweller/datamimic/releases/tag/2.2.0)_

DATAMIMIC 3.0.0 adds a new **time-series generator** to the DSL, makes seeded runs **truly byte-identical** (including source-based pseudonymization), and turns several silent failure modes into clear errors. Plus an honest pass over the README.

---

## ✨ Time-series generation — `<generate start/end/interval>`

Any `<generate>` becomes a time-series loop the moment you add ISO 8601 `start`, `end`, and `interval`. Per iteration the script context exposes a `ts` namespace:

| Variable | Type | Meaning |
|---|---|---|
| `ts.now` | `datetime` | current tick |
| `ts.step` | `int` | position within one series (`0..N-1`) |
| `ts.series` | `int` | which series this row belongs to (`0..count-1`) |

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

**What it guarantees you, the user:**

- **Prefix-stable** — the first N ticks of a series are byte-identical no matter how long you make the total window. Lengthen the window without invalidating your fixtures.
- **Contiguous per series** — series 0 in full, then series 1, etc. Downstream grouping is trivial.
- **Pagination-invariant** — `pageSize` cannot perturb output. Big windows split safely across pages.
- **`count` is orthogonal** — still means outer-loop iterations; total rows = `count × ticks_per_series`. Default `count="1"` keeps single-series fixtures terse.
- **Strict ISO 8601** — `PT1H`, `PT15M`, `PT0.001S` (1 ms), `PT0.000001S` (1 µs, the floor), `P1D`, `P1W`. Months/years and sub-µs intervals are rejected with a clear error.
- **Helpful errors** — every parse error names the offending attribute, echoes your value, and shows a canonical example (e.g. writing `interval="1h"` tells you to use `PT1H`).
- **Composes** with `<key condition>`, `<nestedKey>`, and `<variable source="…">`. The `ts` namespace is visible wherever a script runs.

One primitive serves IoT readings, financial ticks, log streams, smart meters — no per-domain code.

---

## ✨ Model-wide DSL seed — `<setup rngSeed>`

A single seed at the root of `<setup>` propagates a reproducible child RNG to every seed-less `<variable entity="…">` in the model. Per-block `<variable rngSeed>` still overrides. No seed anywhere = wall-clock random (unchanged).

```xml
<setup rngSeed="42">
  <variable name="p" entity="Person"/>   <!-- inherits the seed -->
  <variable name="q" entity="Person" rngSeed="99"/>   <!-- overrides -->
</setup>
```

Consistent attribute name at every level: `<setup rngSeed>`, `<variable rngSeed>`, `<demographics rngSeed>`.

## ✨ Seeded source reads are now deterministic

`distribution="random"` shuffles a data source. Previously, even under a seed, the shuffle order changed every run — silently breaking reproducibility for source-based pseudonymization. Under `<setup rngSeed>`, the shuffle now replays identically across CSV, `.ent.csv`, JSON, SQLite, and cascading `<nestedKey>` reads. Unseeded behaviour is unchanged (privacy-maximized by design).

Combine with `distribution="ordered"` for a stable file-order read.

## 🔒 Determinism, end-to-end

Seeded runs are now **byte-identical across machines and runs** at all three layers: the `generate_domain` facade, every domain service called directly, and every literal generator with a seeded `rng=`. Wall-clock reads in CE prod code are caught by a CI gate, so future changes can't silently drift the clock.

**What this means in practice:** you can put a `content_hash` from a CE run into a regression test, and it stays green forever — until a real data change moves it.

CE is single-process-deterministic. Distributed / multi-process deterministic shuffling remains an Enterprise Platform feature.

---

## 🛠 Improvements you'll notice

- **Clearer errors instead of silent garbage.** Several generators used to fabricate plausible-but-wrong data when a dataset file or key was missing. They now raise a `ValueError` naming the file/key — you find the typo immediately instead of debugging suspicious numbers later. Affects `transaction_generator`, `order.get_shipping_amount`, product rating, insurance premium, coverage count, product nouns, `bank_account` currency, person salutation.
- **No more accidental repeats.** The "pick weighted, avoid immediate repeat" behaviour is now guaranteed (it had two implementations that could still repeat under specific weights).
- **`to_dict()` is consistent.** Nested model fields are now serialized as dicts on `Order` (shipping/billing address, product list), `Doctor.hospital`, and `Transaction.account`. They previously emitted raw model objects — `InsurancePolicy.coverages` was the only one doing the right thing. JSON consumers now see a uniform shape.
- **VN datasets fixed.** Several rows produced corrupt data due to schema mismatches and are now correct.
- **README rewritten.** Compliance framing tightened to what we can actually back ("audit evidence support" rather than "compliance layer"), CE vs EE boundary explicit, the pseudonymization example is now runnable (the old one referenced converters and attributes that don't exist).

## ⚠️ Breaking changes (upgrade order)

1. **Rename `<setup seed>` → `<setup rngSeed>`** (and any `<variable seed>` → `<variable rngSeed>`).
2. **Schema types corrected**: `PoliceOfficer.birthdate` is now `datetime` (was `str`); `InsurancePolicy` date fields are now `date` (were `datetime`). Update consumers that pinned the old types.
3. **`to_dict()` shape**: nested model fields are now dicts on `Order`, `Doctor`, and `Transaction` (see above). Update anything that called `.field` on the result.
4. **Silent fallbacks now raise**: see the list above. If you were relying on a fabricated value, supply the missing data or catch the error.
5. **`seeded_mode` flag removed** from the Python API. Pass `rng=Random(seed)` to mark a generator as seeded. `Random(0)` is now correctly recognised as seeded (it used to be treated as unseeded).
6. **Removed unused helpers**: `EntitySchema.field_names`, `GeneratorUtil.faker_generator` / `get_supported_generators` / `get_all_generator_names`, registry `describe_entity` / `list_entity_names` / `service_path`, `attribute_catalog.spec_to_dict`.

US dataset / country fallbacks and empty `routing_number` for non-US locales are intentionally retained.

## 🐛 Notable fixes

- `Random(0)` is now correctly recognised as a seeded RNG (was treated as unseeded).
- `Transaction.account` is correctly marked optional.
- Set-ordering leak in educational-institution selection (was `PYTHONHASHSEED`-dependent).

## 📦 Build & CI

- GitHub Actions on Node 24.
- TestPyPI auto-uploads have been removed; tags continue to publish to prod PyPI.

## Known gaps

- **Multi-process determinism** (`numProcess > 1`) is single-process-deterministic only; cross-process deterministic shuffling remains an Enterprise Platform feature.
- Locale data still incomplete: `categories_{FR,GB,ES}.csv`, `product_nouns_*_VN.csv`, DE `administration_office` phone field. Predate 3.0.0 — surfaced by the new errors.

---

**Commits:** `5cafb56` · `3ffaf2c` · `e97e12e` · `f6e77e0` · `b9238e7` · `da591db` · `665b463` · `abbf034`
**Full diff:** [`2.2.0...3.0.0`](https://github.com/rapiddweller/datamimic/compare/2.2.0...3.0.0)

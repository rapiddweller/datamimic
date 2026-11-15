# Determinism evidence for CE

This page moved from the README. The evidence is for CE only. The DATAMIMIC Enterprise Platform runs on a separate engine and is outside it.

## Why deterministic generation matters

Most test data tools produce random output. That breaks regression tests, audit trails, and cross-team reproducibility.

**How it works in CE:**

- Set `<setup rngSeed="N">` and seeded generation replays on the tested runtime profiles, including generator, entity, and script-expression paths. Seeded date-derived values use the deterministic clock anchor; without a seed, generation is not replay-stable.
- `distribution="ordered"` reads a source in file order; `distribution="random"` shuffles it, reproducibly with a seed.
- The Python facade `generate_domain(...)` returns `determinism_proof.content_hash`: the same hash means the same data.
- The committed replay model covers every registered literal generator except the database-backed `SequenceTableGenerator`, plus the supported dynamic script-global families. It is replayed in two separate processes on each CI run ([`test_determinism_seed_scenarios`](https://github.com/rapiddweller/datamimic/tree/development/tests_ce/integration_tests/test_determinism_seed_scenarios)).

The CE seeded-runtime guarantee is scoped to the tested profiles. CI runs seven x64 cells: `ubuntu-22.04` with Python 3.11, 3.12, and 3.13 in `Etc/UTC`; Python 3.11 in `America/Los_Angeles`; and `windows-latest` with Python 3.11 in `UTC` and `Pacific Standard Time`. These six cells use `uv sync --resolution highest`; a representative `ubuntu-22.04`/Python 3.11/`Etc/UTC` cell uses `uv sync --resolution lowest-direct`. Each cell records its exact interpreter and installed package versions in the uploaded artifact and job log. Other Python versions and dependency resolutions are outside this matrix. `uv.lock` is intentionally untracked. The committed goldens and cross-cell fan-in, rather than production dependency pinning, define the byte-identical gate.

The DATAMIMIC Enterprise Platform behavior is outside this CE evidence.

```python
from datamimic_ce.domains.facade import generate_domain

request = {
    "domain": "person",
    "version": "v1",
    "count": 1,
    "seed": "regression-suite-42",       # same seed → replayable on the tested profiles
    "locale": "en_US",
    "clock": "2025-01-01T00:00:00Z"      # fixed clock = stable time context
}

response = generate_domain(request)
# response["determinism_proof"]["content_hash"] is stable for the same CE version, request,
# seed, and clock within the tested compatibility boundary.
```

Direct service use is deterministic for repeated runs with the same seeded RNG and configuration:

```python
import random
from datamimic_ce.domains.finance.services import CreditCardService

# Same seeded Random → same CreditCard fields for the same configuration.
card_a = CreditCardService(rng=random.Random(42)).generate()
card_b = CreditCardService(rng=random.Random(42)).generate()
assert card_a.bic == card_b.bic and card_a.card_number == card_b.card_number
```

## Determinism evidence

The CI gate compares seeded runtime manifests and committed goldens across the seven
matrix cells above. Its coverage is:

| Scope | Evidence |
|---|---|
| Facade API | 4/4 registered domains |
| Entities | 23/23 entities, selected attributes |
| Literal generators | 34/35; database-backed `SequenceTableGenerator` is excluded from this byte hash and covered by external-service DSL tests |
| Seeded Safe Globals | 27 representative paths across `datetime`, `fake`, `math`, `numpy`, `pandas`, `random`, and `uuid` |
| Rejected entropy | 5 committed negative DSL descriptors |
| Encoding | 1 canonical UTF-8 probe |

Arbitrary exporter bytes/encodings and the Enterprise Platform are outside this
CE gate.


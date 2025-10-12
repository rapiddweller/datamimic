# Controlling Generator Caching

Datamimic caches generator instances globally to avoid unnecessary
initialisation. This behaviour is configurable via a `cache_in_root`
attribute available on generator classes.

## cache_in_root Attribute

All generators derived from `BaseLiteralGenerator` default to
`cache_in_root = True`. When `True`, the generator instance is stored in
`context.root.generators` and reused whenever a generator with the same key is
requested.

To opt out of caching, override the attribute:

```python
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class TransientGenerator(BaseLiteralGenerator):
    cache_in_root = False

    def generate(self):  # pragma: no cover - example snippet
        ...
```

Generators with `cache_in_root = False` are recreated for every request and are
not stored in the root context.

## Usage

`GeneratorUtil.create_generator` automatically respects the `cache_in_root`
flag. Tasks such as `KeyVariableTask` and `GeneratorTask` delegate caching
responsibility to this utility, ensuring consistent generator lifecycles
throughout the framework.

## RNG Injection and Dataset I/O (SOC)

- Inject a `random.Random` into generators (e.g., `__init__(..., rng: random.Random | None = None)`) and use `self._rng` for all randomness. Do not use module‑level `random` in shared code.
- Keep dataset I/O in generators; models must be pure (no file reads, no logging). Resolve paths via `datamimic_ce.utils.dataset_path.dataset_path` or the lightweight loaders.
- When services need to advertise supported datasets, compute them via `compute_supported_datasets([...], start=Path(__file__))`.

## Seeding Patterns for Reproducibility

- Prefer constructor signature `__init__(..., rng: random.Random | None = None)` and store `self._rng = rng or random.Random()`.
- Propagate the same `self._rng` to all sub-generators to keep a single deterministic stream.
- Expose an `rng` property for models to consume randomness via their generator, never directly via module `random`.

Example:

```python
class FooGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        self._dataset = (dataset or "US").upper()
        self._rng = rng or random.Random()
        self._child = ChildGenerator(dataset=self._dataset, rng=self._rng)

    @property
    def rng(self) -> random.Random:
        return self._rng
```

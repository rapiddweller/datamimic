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
- Keep dataset I/O in generators; models must be pure (no file reads, no logging). Resolve paths via `datamimic_ce.domains.domain_core.datasets.path.dataset_path` or the lightweight loaders.
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

## Global increment counters

`GlobalIncrementGenerator` emits a monotonic sequence starting at 1 for each
qualified generator field in one root setup context. Pages and repeated nested
parents continue that field's counter. Distinct qualified fields have separate
counters, so their values can overlap; a new run starts fresh. Included setup
files clone their owning root context and keep independent counter state. For
example, including the same two-row descriptor twice can emit `1, 2, 1, 2` for
the same qualified field; this is not a descriptor-wide uniqueness guarantee.

CE executes a generate containing this generator in one process, including when
it appears in nested generates, conditions, nested keys or XML attributes. This
overrides both multiprocessing and Ray worker requests before workers start.
The process-local registry cannot reserve safe disjoint ranges for arbitrary
nested row counts. Explicitly referenced named global-increment instances in
the setup registry use the same serial policy. An unrelated or unused generator
alias does not force serial execution. Ordinary `IncrementGenerator` keeps its
existing page ranges and worker behavior. Seeded runs still replay identically.

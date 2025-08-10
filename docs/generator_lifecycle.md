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
from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator

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

# Draft ArchKeel issue: Decide typed iterator unions at boundary_types

Status: not filed. The GitHub integration returned 403 on `create_issue`; the
local `gh` token is invalid. Proposed labels: `rule-gap`, `agent-workflow`,
`enhancement`.

`boundary_types` can name this position now, but it still cannot decide it.

DATAMIMIC CE Experiment 2, ArchKeel 0.6.1, rule `DOMAIN-API-TYPES` on
`datamimic_ce.domains.api`:

```python
def iter_generator_types() -> Iterator[type[BaseLiteralGenerator | BaseDomainGenerator]]:
    ...
```

The 34 built-in classes are subclasses of those two public base classes.
Full-package MyPy passes, and a negative MyPy probe rejects an unrelated
class. ArchKeel parses all 474 files, reports 0 violations, but marks this
return position `generic`: `unknown_positions=1`, `declared_rules=UNKNOWN`.
`Iterator[type[BaseLiteralGenerator] | type[BaseDomainGenerator]]` has the
same result. We reverted the typing change rather than call the boundary
proven or widen the contract. The local evidence is Step 08C21.

Expected: decide standard `Iterator`, `type`, and local union members
recursively. A public member should pass; a proven private member should
violate; an unresolved member should remain UNKNOWN. Cover both equivalent
spellings with positive, negative, and undecidable fixtures. Do not turn this
into a blanket PASS for generics.

Related: [#127](https://github.com/rapiddweller/archkeel/issues/127) added
per-position evidence. This is the remaining decision gap, not another
request for aggregate reporting.

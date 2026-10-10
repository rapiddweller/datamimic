# Step 08C16: type domain data and JSON dispatch

## Change

- Replaced open-ended domain payload and result annotations with explicit JSON and model types.
- Kept JSON Schema as the validation source; Pydantic constructs the four typed request objects only
  after schema validation.
- Typed domain entities, converters, locale data, demographic sampling, and deterministic helpers.

## Evidence

- ArchKeel violations: 202 -> 91; 111 baseline fingerprints resolved and 0 added.
- Domain findings: 119 -> 8 before the final entity-cache cleanup.
- Independent review found no concrete API or behavior regression.
- Domain/API/demographic review set: 290 passed, 1 skipped. Integrated focused set: 87 passed.
- Ruff passed. Full-package mypy reported only the two optional Ray imports owned by the parallel
  Runtime lane.

The generic `TypeAdapter(request_cls).validate_python(...)` call adds one unresolved-call
measurement in this isolated slice. Duplicating the schema fields into four constructors would
make the validation contract less reliable. The integrated Runtime slice reduces the same
measurement from 1,397 to 1,288, so no larger measurement budget is accepted.

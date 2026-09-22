# Experiment 2 decision log

## D1 — `services` is deleted

**FACT:** `datamimic_ce/services` contains only `source_script_evaluator.py`.

**Decision:** move template evaluation to `engine.runtime.evaluation`; do not create a replacement
service layer.

## D2 — Authoring projects owner facts

**FACT:** the element registry, Pydantic models, constraints, generators, exporters, and domain
registries already own the executable facts.

**Decision:** Authoring owns intent and projection. It does not maintain a second DSL or capability
catalog. Bounded execution crosses `engine.runtime.api` only.

## D3 — types are local

**Decision:** each component owns its contracts. There is no shared `types`, `models`, `common`, or
`foundation` package. Cross-component signatures expose types from the owning component's
`contracts.py`.

## D4 — public APIs are per component

**Decision:** architecture components expose `api.py` and `contracts.py`; ordinary subpackages do
not get ceremonial facades. External Python compatibility paths remain where documentation proves
they are public.

## D5 — `domains` remains top-level

**FACT:** README and developer documentation import domain services and models directly.

**Decision:** keep `domains` as a first-class public component. Moving it under `engine` would add a
large compatibility layer without making its ownership clearer.

## D6 — domain datasets use a narrow IO facet

**FACT:** 29 domain modules load packaged CSV or JSON datasets. Parsing and caching those files is
IO behavior; the dataset contents and selection logic belong to `domains`.

**Decision:** allow `domains` to depend on `io` only through `engine.io.dataset_api`, which exposes
file loading and caching but no database client. Keep domain-specific paths, fallback, weighting,
and selection in `domains`. Do not add a shared foundation or duplicate the parsers.

## D7 — logging uses the standard library directly

**FACT:** all affected modules use the same named `logging.Logger` object. ArchKeel 0.6.0 resolves
methods on the former imported module variable but not on `logging.getLogger(...)` bindings.

**Decision:** remove the cross-component runtime logger dependency and use
`logging.getLogger("DATAMIMIC")` directly. Accept the resulting call-resolution measurement reset
as an analyzer limitation; do not rewrite ordinary logger calls as unidiomatic class-method calls.

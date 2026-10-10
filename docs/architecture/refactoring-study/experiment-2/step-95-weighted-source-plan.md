# Step 95: weighted CSV result

Base `f2479142`. Astra approved text/null as this file source's result domain.
CSV cells are strings; IO selects them, Runtime converts to descriptor types.
Nested-key shape typing is a separate candidate, not included.

## Task 1: Independent tests

Own only `tests_ce/unit_tests/test_weighted_data_source.py`, testing
`datamimic_ce.engine.io.data_sources.weighted_data_source.WeightedDataSource`.
Its public `generate() -> str | None` selects CSV text/null; Runtime converts
descriptor types. Challenge the real reader before assuming that domain.
No production, fixture, oracle, contract or Git edits.

- Real CSVs: optional/no header, comma/pipe, numeric/boolean-looking text,
  empty text, duplicate values, zero weights and missing cells where supported.
- Fixed seeds: compare selected sequences and final Random state against the
  unchanged choices expression. Preserve exactly one choices call per draw.
- None and string subclasses retain identity. Injected integer, float, list
  and arbitrary-object results fail with the existing outer ValueError and
  TypeError("Weighted CSV values must be strings or None") as cause.
- Empty/all-zero/malformed weights retain original failure behavior and timing.
- Check the exact `str | None` public return annotation. Record genuine RED,
  already-passing compatibility cases and any unsupported ordinary CSV shape.

## Task 2: Independent implementation

Own only `datamimic_ce/engine/io/data_sources/weighted_data_source.py`.
Change `generate(self) -> object` to `generate(self) -> str | None`.
Inside its existing try, assign the existing choices expression once to
`value: object`; return unchanged when None or str, otherwise raise
TypeError("Weighted CSV values must be strings or None"). Keep the enclosing
exception message/cause wrapping, reader, normalization and RNG use unchanged.
No conversion, cast, helper, cached second value list, allowance or checker edit.

CE5 contraction: private/monkeypatched non-text values now fail rather than
escape. External use is UNKNOWN. Ordinary weighted DSL must remain unchanged.

## Root acceptance

Freeze eight existing descriptors and four Authoring projections before code.
Run independent tests, unchanged weighted/header/guard suites and seeded DSL
replay; full Make unit, lint/MyPy, definition/cycle gates and fresh released
ArchKeel 0.8.4 scan. Expect only the weighted `object` return finding to resolve;
do not claim that before measurement. No new findings/UNKNOWNs or baseline growth.
Fresh Astra review; commit/push only this coherent slice to Draft PR274.
Primary dirty drafts stay untouched. Full parity/navigation/goal remain open.

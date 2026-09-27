# Step 12: reviewed target and physical migration

Date: 2026-09-27. Status: in progress, not target acceptance.

## Definition

`eb4733dd` freezes Astra's delegated decisions, 22 canonical contract scopes and
the explicit dispositions of all 488 source Python modules at `3b844b50`.
The final map has 486 non-demo target modules, including explicit splits,
merges, removals and one new typed IO boundary. Nine demo Python modules remain
visible but outside physical regrouping.

The independent definition gate passes. Before production moves, physical
acceptance correctly failed with 260 missing target paths and 253 legacy paths.
Empty placeholder modules cannot satisfy the physical check. The contract CI
checkout now fetches the frozen source history required by that check.

The large definition diff is contract/audit data, not additional runtime code.
Generated aggregate review copies and browser artifacts are not part of that
commit. Historical baselines and review hashes remain unchanged.

## Behavioral baseline

- Serial non-service baseline: 3,858 passed, 28 skipped, two serializer warnings.
- 930 descriptor XML files and seven intent models hashed before moves.
- Fresh Step-0 inventory: 454 captured, 62 expected errors, 16 non-descriptors,
  76 unsuitable for standalone execution and 322 initially unverified.
- Those categories are not execution verdicts: consumer tests and dynamic demo
  parameterization cover additional descriptors. External-service evidence
  remains separate; an unavailable or unrun path is not a pass.

## First slice: Domains and packaged resources

Luna moves single-destination Domain modules and their consumers. Terra owns
independent QA; root reviews and accepts. Semantic splits and merges remain
later slices. No XML, intent-model or oracle expectation changes are authorized.

The first slice moves 70 modules. Physical gaps decrease from 260 missing / 253
legacy paths to 190 missing / 183 legacy paths. This is progress, not completion.

Review caught a prefix-replacement error before acceptance. Exact descendant
imports must win over an initializer's package move; deferred merge sources
must not be rewritten to nonexistent destinations.

The installed-wheel test caught an actual packaging defect: broad namespace
discovery included `docs/` and `test-artifacts/`. Discovery is now restricted
to `datamimic_ce*`, and test artifacts are excluded from the source archive.
Coverage excludes the same runnable examples at their new path; the threshold
is unchanged. The wheel test runs in the existing unit CI job.

Terra's first full run found three stale locale test imports, now corrected,
plus the intentionally failing final-layout test. Root removed 31 unrelated
formatter-only changes after checking AST identity. Apart from import moves,
the behavior-AST review found only dataset/schema lookup repairs and one updated
Python extension path in reference text.

Astra corrected D18 after checking the actual service constructors: a subclass
type does not describe their different constructor signatures. The premature
annotation and local callable alias were removed. A following slice will rename
the existing lookup to `get_entity_service_factory`, preserving its explicitly
dynamic callable boundary without a wrapper or private cross-component import.

LOCAL VERIFIED: 22 contracts parse and 21 nested mounts load without errors;
definition Make target passes. Independent wheel check passes outside the
checkout: exact Python inventory, real dataset generation and schema loading,
explicit resource override and missing-override behavior. The first serial run
had 3,854 passes, 28 skips and four failures as described above; ten focused
tests pass after the import repair. Full-package Ruff and Mypy pass (488 files).
The raw Step-0 comparison reports two differences, not a clean comparison:
unseeded MemStore count 19 versus 15 (Amendment 13 governs same-run invariants),
and the sole capability field `/schema_version` changing from
`4.3.1.dev89+dirty` to `4.3.1.dev130+dirty` after package metadata refresh.
No capability content beyond that build identity differs. Terra reproduced
unseeded counts 19 and 17; root reran the existing bounded count/relationship
test successfully. These are classified differences under Amendment 13, not
a silently green raw comparator. The Domain slice is accepted with that stated
evidence; final architecture and external-service acceptance remain open.

CI-ONLY VERIFICATION: no new remote run yet. No PR merge or release performed.

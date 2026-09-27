# Step 12: reviewed target and physical migration

Date: 2026-09-27. Status: in progress, not target acceptance.

## Definition

`eb4733dd` freezes Astra's delegated decisions, 22 canonical contract scopes and
the explicit dispositions of all 488 source Python modules at `3b844b50`.
The amended map has 487 non-demo target modules, including explicit splits,
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

## Second slice: DSL, IO, Runtime and Python entrypoints

160 single-destination moves are implemented. Root's AST comparison against
`e884e763` finds no production changes beyond imports. Physical gaps are now
29 missing target paths and 21 legacy paths; semantic splits remain pending.
The original 930 XML descriptors, seven intent models and violation baseline
are unchanged. Two embedded Python imports in verification runners follow the
new Python entrypoint; their expectations are unchanged.

Astra corrected two decisions before the semantic slices:

- Keep `derived_facts` in Authoring Domain. DM408 and application results consume
  the same semantic derivation; moving it to Projection creates a cycle.
- Keep a meaningful Runtime task initializer importing the new registry once.
  Cold multiprocessing and Ray workers enter below the lifecycle runner.
  This adds one target module, taking the total from 495 to 496. DSL parser
  composition remains explicit in the descriptor parser.

The one-shot mover scanned too broadly and also rewrote 364 generated
`build/lib` Python copies. The generated directory was quarantined recoverably
at `/private/tmp/ce-s2b-build-cache.TxV6P1/build`; the mover was retired. Subsequent
work must use tracked inputs and explicit destinations, never recursive checkout
rewrites. No descriptor or captured baseline was affected.

LOCAL VERIFIED: recursive definition tests pass; full-package Ruff and Mypy
pass (488 files). Luna reports 1,201 unit passes / 11 skips before the final
path corrections and 24 affected authoring/determinism passes afterward.
Independent QA passed 147 registry-owner tests and the cold CLI entrypoint.
The serial run had 3,857 passes, 28 skips, one deselected final-layout check,
and one failure: the clock gate still allowed telemetry at the old Python
entrypoint path. After updating that exact path, 480 clock/entrypoint checks
pass. The failed full run remains recorded; it was not rerun wholesale.

Step-0 retains all 930 statuses. Raw comparisons remain red only for the known
unseeded MemStore count variance and build-version identity. S2A to S2B changes
capabilities only at `/schema_version` (`dev130` to `dev131`), not capability
content. XML/model hashes remain exact. This movement-only slice is accepted
with these bounded results; service and final architecture acceptance remain open.

CI-ONLY VERIFICATION: no new remote run.

## Third slice: neutral contracts and generator metadata

Random-source primitives now live in `randomness.py`; the unchanged EntityValue
ABC belongs to IO. Domain generation types and signature metadata no longer
depend on the high-level DSL API. The existing service lookup is renamed to
`get_entity_service_factory`, without changing constructor filtering or its
explicitly dynamic callable return. Old modules/exports are removed, not shimmed.

Root verified identical ASTs for all six moved declarations, allowing only the
approved function rename. Terra's checks cover real Person/Patient/BankAccount
construction, rejected explicit keywords, injected options, the actual EntityValue
ABC, capability ordering/fallback and exact RNG state after 25 sampling draws.

Astra also withdrew the planned root dotenv move after tracing MCP and standalone
Domain entrypoints. Its existing package bootstrap remains unchanged: relocation
would change lookup/timing and require the wrong Domain-to-Runtime dependency.
The target file set remains 496; this removes a needless behavior split.

LOCAL VERIFIED: Luna's 35 unit and 27 integration/manifest checks pass; Terra's
independent 23 focused and 556 wider checks pass. Full-package Ruff/Mypy pass.
S3A versus S2B: 930 descriptors compared, zero differences, two existing normalized
or optional variances; capability payload and hash are identical. Comparison
with the original retains the previously recorded unseeded/build-identity deltas.
XML/models/baseline are unchanged. The slice is accepted, not the final target.

CI-ONLY VERIFICATION: no new remote run.

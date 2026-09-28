# Step 12: reviewed target and physical migration

Date: 2026-09-27. Status: in progress, not target acceptance.

## Definition

`eb4733dd` freezes Astra's delegated decisions, 22 canonical contract scopes and
the explicit dispositions of all 488 source Python modules at `3b844b50`.
At that freeze the map had 487 non-demo target modules, including explicit splits,
merges, removals and one new typed IO boundary. Nine demo Python modules remain
visible but outside physical regrouping.
The reviewed exporter amendment below reduces the current target to 486 core
modules plus those nine demo scripts.

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

Separate pre-existing finding: [CE #275](https://github.com/rapiddweller/datamimic/issues/275)
records a bounded reproduction of shuffled selection hanging on a one-shot
iterator. The function is unchanged from the frozen source; no end-to-end DSL
reachability is claimed. It is not silently fixed as part of the relocation.

## Fourth slice: parser composition and connection profiles

DescriptorParser composes the ordered built-in registry explicitly. Base dispatch
no longer imports concrete parsers. IO owns profile file loading; DSL owns the
typed loader callback and credential merging. Runtime and Authoring inject the
loader. The old parser utility class and package re-export initializer are removed.

Independent tests preserve descriptor/current-directory/home lookup order,
FileNotFoundError-only fallback, property precedence and aliasing, nested includes,
extension calls and cold composition. No descriptor, intent model or baseline changed.

LOCAL VERIFIED: 124 serial parser/authoring regression tests pass; full-package
Ruff and Mypy pass (490 files). Step-0 retains 454 captured, 62 expected errors,
16 non-descriptors, 76 unrunnable and 322 unverified entries. S3B versus S3A has
only the known Amendment-13 unseeded count variance; its bounded invariant passes.
The original comparison additionally retains the documented capability build
identity difference. This is not a claim that all 930 entries executed.

CI-ONLY VERIFICATION: no new remote or external-service run.

Astra also corrected the pending exporter target after tracing its dependencies:
smoke execution joins the existing registry instead of creating a diagnostics-to-
registry cycle. Exporter configuration becomes scalar-only; the IO-owned context
protocol remains only at composition. The target now has 495 Python modules,
including nine packaged demo scripts. The recursive definition gate passes.

## Fifth slice: statement traversal

Statement/CompositeStatement now own only the common tree shape. Generate and
Condition live in their respective families; high-level traversal imports those
families, not the reverse. The old descendant-aware base methods and paths are
removed. `get_nearest_generate_statement` names the existing nearest-ancestor
behavior correctly; a Generate itself still returns no ancestor. Condition exposes
its existing executed-branch set as a typed field, without copying or sorting it.

LOCAL VERIFIED: independent baseline tests passed before implementation. Afterward,
147 relevant tests pass with 11 existing skips; full-package Ruff/Mypy pass (491
files), as does the recursive definition gate. All Step-0 statuses and XML/model
hashes remain unchanged. The only comparisons are the previously recorded unseeded
count and build-identity differences. Physical gaps are 17 missing / 13 legacy paths.

The original source also passed isolated Docker service verification: 164 tests
passed, four existing skips; the separate local-profile PostgreSQL test passed.
These are the before-side assertions, not yet old/new database-output equivalence.
No shared database was touched. Details are in the QA service-baseline receipt.

CI-ONLY VERIFICATION: no new remote run. Strict target validation remains UNKNOWN
because the IO boundary and task registry target modules are not implemented yet.

## Sixth slice: contexts and runtime-owned generators

Context and SetupContext share their cohesive owner; expression globals take an
explicit RNG and lazy Faker supplier without importing Context. GlobalIncrement
state belongs to Runtime storage, its generator to value construction. Domain and
Runtime capability inventories still expose each generator exactly once.

Review caught and corrected a missing constructor-time counter registration.
Astra also rejected deleting the generator's context reference: actual old/new
probes showed different deepcopy graphs and client-disposal hooks despite matching
counter values. The reference is retained; only the unused scalar flag is removed.

LOCAL VERIFIED: Terra's independent 148 tests pass with 11 existing skips;
21 inventory/replay tests pass after strengthening the duplicate-name assertion.
Full-package Ruff/Mypy and both definition tests pass. XML/model hashes and the
violation baseline remain unchanged. The target has 15 missing / 11 legacy paths.

The final full Step-0 capture has one missing child result: the credit-card run
logged 100 generated rows and exited zero, but returned no result marker. Three
isolated retries exactly match its previous capture. No capture was overwritten.
All other differences are the recorded unseeded MemStore count variation; its
same-run invariant passes. Projection payloads are identical to the preceding
slice; comparison with the original retains the documented build identity delta.

Real isolated Linux spawn and Ray workers reproduce the frozen GlobalIncrement
sequence. One Ray attempt failed during Raylet registration; an unchanged retry
passed. This is not a claim of uninterrupted worker reliability. The pre-existing
cross-worker duplicates (`1,2,1,2`) are recorded in [CE #276](https://github.com/rapiddweller/datamimic/issues/276),
separate from this behavior-preserving move. Worker details are in the QA receipt.

CI-ONLY VERIFICATION: no new remote run; final service/worker acceptance remains open.

## Seventh slice: non-exporter TaskUtil ownership

Task dispatch now calls the existing dispatcher directly. Condition and source
template evaluation live in Scripting; converter construction and scalar
random defaults live with value construction. Generate retains selector
interpolation at its original count-resolution point. `TaskUtil` now contains
only the exporter/page code reserved for the next slice.

Terra independently verified 99 affected tests with 11 existing skips and
added pre-move exporter-dispatch tests. Root reviewed the call sites and caught
one vacuous `MagicMock` assertion; it now patches the actual dispatcher.

The first broad run had 1,932 passes, 13 skips and three failures. One test
captured no log after an earlier engine run disabled propagation; it now
enables propagation only for that test. The MCP SSE test could not bind a
loopback port in the sandbox and passed outside it. The datetime test compared
the engine's historical UTC date with the host's local date. Astra checked the
frozen clock/generator AST and a timezone-boundary probe: production already
used UTC. The test now bounds the generated date by UTC before/after execution,
with a fixed-instant regression. No descriptor or production clock changed.

LOCAL VERIFIED: the repeated broad serial suite passes 1,936 tests with 13
existing skips and two serializer warnings; full-package Ruff/Mypy pass (492
modules); recursive target definition passes. A four-job Step-0 capture has all
930 inventory entries and 454 captured runs, with no lost child result. Its
only runtime comparison difference against S3C is the previously approved
unseeded MemStore count; the same-run count invariant passes. Against the
frozen source, the historical capability build-identity difference remains.
All 930 XML and seven intent-model hashes match their frozen manifests.
The physical target is still incomplete: 15 missing and 12 legacy modules
after Astra's source-capability correction. The ArchKeel candidate scans all
492 Python files in about 10 seconds but exits 2/UNKNOWN because required
future IO-boundary and task-registry subjects are absent. It is not a green
target gate or a verified finished HTML report.

CI-ONLY VERIFICATION: no new remote run. The isolated service after-side and
final old/new database result comparison remain open.

## Eighth slice: source and target routing ownership

`StatementUtil` is gone. DSL owns target-token parsing; IO owns scalar source
and target resolution and the existing AST target parser. Callers use those
functions directly, without an old-path class. The optional MemStore entity
still reaches its historical error/length paths; no empty-string fallback or
new assertion changes the result. Astra approved the ownership after reviewing
the nullable path and Mongo's explicit-collection rule.

LOCAL VERIFIED: 1,940 non-service tests passed, 13 existing skips; full-package
Ruff/Mypy and Pylint's import-cycle gate pass. Both recursive definition tests
pass. The physical target check remains red: 12 missing target modules and 11
legacy/unowned modules. All 930 XML and seven intent-model file hashes match
the frozen inputs. Step-0 retained every status (454 captured, 62 expected
errors, 16 non-descriptors, 76 unrunnable, 322 unverified). Its raw comparator
reports the known unseeded MemStore `te` count variance, whose same-run bounded
test passes, and a capability-text change. Against the preceding slice only
five capability description entries change: they no longer cite the deleted
`StatementUtil`; compiler, authoring reference and scaffold projections are
identical. Against the frozen source the prior build-version identity delta
remains. The raw comparator therefore exits 1; it is not called green.

CI-ONLY VERIFICATION: no new remote or after-side external-service run. The
exporter, source-boundary and task-registry slices remain open.

## Ninth slice: exporter ownership and page order

`ExporterUtil` and the remaining `TaskUtil` code are gone. IO owns the exporter
registry, row conversion, concrete dispatch and smoke export. Generate owns
parent/child page order. Buffered exporter configuration contains scalar values,
not a Runtime context. Tests now call the actual IO and Generate operations;
tests for the deleted, unused serializer/path-format helpers were removed.

Astra found a declared Generate child-cycle during review: the worker calls
`export_order`, while `task.py` selects workers. Amendment 24 gives export order
its own child component without changing a file or runtime behavior. Amendment
23 publishes the exact IO conversion function and tests its failure before
cache lookup, page-count mutation and nested writes.

LOCAL VERIFIED: Terra's independent focused suites passed 173 exporter/authoring/
source tests, 15 nested-export tests and 21 Generate tests (11 skips). Root's
serial non-service sweep passed 1,920 tests, 13 skips and two existing Pydantic
warnings. Full-package Ruff/Mypy (494 modules), Pylint import-cycle check and
both recursive definition tests pass. The physical target remains red: nine
missing target modules and eight legacy/unowned modules. All 930 XML and seven
intent-model hashes match the frozen inputs. Step-0 retained every status
(454 captured, 62 expected errors, 16 non-descriptors, 76 unrunnable, 322
unverified). Its raw comparison exits 1 for the approved unseeded MemStore
`te` count variance (17 to 15; the same-run bounded invariant passed) and
two capability provenance strings: DM401 now names the IO target parser,
DM402 names source routing instead of the removed utility classes. Compiler,
Authoring reference and scaffold projections are unchanged. This is a
classified difference, not a green raw comparison.

The after-side isolated Docker/OrbStack service suite used a fresh private
stack and the committed `0a7094a0` source snapshot: 164 passed, four skipped.
Its 168 JUnit case identities and outcomes exactly match the frozen before
suite; 14 SQL Server-version warnings do not change assertions. This is not
a direct comparison of persisted database values.

CI-ONLY VERIFICATION: no new remote run. ArchKeel still exits 2/UNKNOWN because
`runtime.tasks.registry` is absent. Source boundaries, task registry, direct
database-output parity and complete target acceptance remain open.

## Tenth slice: source-capability ownership

The unchanged source-format/capability catalog moved from DSL model constraints
to DSL vocabulary. Production and test imports now use its owner; `dsl.api`
keeps its existing public names. There is no old-path forwarding module.
Astra required the exact vocabulary leaf in the root DSL public list, added
under Amendment 21. No runtime dispatch or descriptor changed in this slice.

LOCAL VERIFIED: Terra's independent focused suite passed 175 tests. Root's
serial non-service sweep passed 1,928 tests, 13 skips and two existing Pydantic
warnings. Full-package Ruff/Mypy (494 modules), Pylint's import-cycle gate and
the recursive definition gate pass. The moved catalog is byte-identical to its
prior file. The physical target still fails: eight missing target modules and
seven legacy/unowned modules. ArchKeel's candidate validator still reports
UNKNOWN solely because `runtime.tasks.registry` has no scanned module. All
930 XML and seven intent-model hashes match the frozen files. Step-0 retained
all status counts (454 captured, 62 expected errors, 16 non-descriptors,
76 unrunnable, 322 unverified); all four projection hashes are identical to
the preceding slice. The raw comparator exits 1 for one unseeded Condition demo
whose optional `else-if_true` field was absent in this capture. Three isolated
reruns on the same code contained that field; this is a classified stochastic
variance, not a green raw comparison. No new service run was required for this
byte-identical catalog move; the S3F2 after-side service result remains the
latest service evidence.

CI-ONLY VERIFICATION: no new remote run. IO source boundaries, the task
registry, direct database-output parity and complete target acceptance remain
open.

## Eleventh slice: cold task registry and IO source ownership

The task registry now lives in `runtime.tasks.registry`; the package initializer
imports it so fresh multiprocessing workers still register tasks. A real
two-worker descriptor test proves custom registration in worker processes.
The source-format catalog stays in DSL vocabulary. IO now owns source counting,
nested-key file/memstore reads, reference row fetching and selection. Runtime
still resolves statements, expressions, clients, seed and cache. No old-path
forwarding module was added. Independent tests pin file-before-provider order,
the Mongo error path, and lazy reference RNG behavior. Astra rejected a proposed
dict pre-scan guard: that scan historically probes providers before the loader
rejects the source, so the guard and its test were removed.

LOCAL VERIFIED: 1,940 non-service tests passed, 13 existing skips and two known
Pydantic warnings; full-package Ruff/Mypy (497 modules), Pylint import-cycle
check and both recursive definition tests pass. The physical target still has
five missing modules and seven legacy/unowned modules. All 930 XML and seven
intent-model hashes match the frozen files. Step-0 inventoried all 930 XML
files; one otherwise successful multiprocessing descriptor lost its child result
under the four-job sweep (453 captured, 77 unrunnable), then passed in an
isolated repeat. The other two differences from the prior slice are unseeded
Condition and MemStore value/count variance; all four capability/compiler/
authoring projection hashes match the prior slice. The raw comparison exits 1,
so this is classified evidence, not a green equality claim.

Released ArchKeel 0.8.0 exits 2/UNKNOWN on this full CE scan because its
bundled analyzer exceeds its fixed 60-second deadline (tracked as #192). A
newer local candidate completes coverage but reports 13 target modules not
built yet, two stale graph edges and 132 public-interface diagnostics; these
must be resolved individually after the remaining physical moves. Neither run
is a passing target gate. The latest isolated service-backed suite remains the
S3F2 result, not a verification of these source moves.

CI-ONLY VERIFICATION: no new remote run. Chunk/variable source boundaries,
direct persisted database parity and complete target acceptance remain open.

## Twelfth slice: chunk source window

`ChunkSourceReader` moved into Runtime tasks. IO owns only the selected
`ChunkSourceWindow`; it receives an already loaded pool and seed, selects once,
and returns shallow page slices. Runtime keeps lazy first-page loading, source
evaluation and seed timing. The old path was deleted without a forwarding
module. Astra approved this smaller boundary; independent QA added cumulated,
unique and exhaustion cases before the move. Terra found no actionable
after-side defect.

LOCAL VERIFIED: 43 focused source/DSL tests and the serial non-service sweep
(1,943 passed, 13 existing skips, two known warnings) pass. Full-package
Ruff/Mypy (498 modules), recursive definition and Pylint import-cycle gates
pass. The physical target still has three missing modules and six legacy/
unowned modules. All 930 XML and seven intent-model hashes remain unchanged.
Step-0 retained all status counts (454 captured, 62 expected errors, 16
non-descriptors, 76 unrunnable, 322 unverified). Compared with S3G1, only the
previously classified unseeded MemStore `te` count varies; all four projection
hashes match. The raw comparator exits 1, not a green exact-equality result.

CI-ONLY VERIFICATION: no new remote or after-side service run. Variable source
ownership, Runtime router relocation, direct persisted database parity and
complete target acceptance remain open. Released ArchKeel 0.8.0 remains
UNKNOWN at its fixed 60-second analyzer deadline (#192).

## Thirteenth slice: variable source reads

Runtime retains variable planning, selector validation, seed, cache, lazy
evaluation and weighted-source policy. IO now owns file, database and MemStore
reads and query paging. The old Runtime source path is gone, with no forwarding
module. Luna pinned empty versus materialized pools before the move; Terra's
independent review found no P1/P2 semantic regression for valid DSL.

LOCAL VERIFIED: 1,945 serial non-service tests pass, with 13 existing skips
and two known serializer warnings; 113 focused source tests, full-package
Ruff/Mypy (499 modules), Pylint import-cycle and both recursive definition
checks pass. The 930 XML and seven intent-model hashes are unchanged.
Step-0 retains 454 captured, 62 expected errors, 16 non-descriptors, 76
unrunnable and 322 unverified entries. Against the prior slice, its raw
comparison exits 1 for two known unseeded differences: a conditional field
appears in one demo capture and the MemStore `te` row count changes from 9
to 13. An isolated same-code repeat still captures the conditional field
and the MemStore count of 13. All four projection payloads match the prior
slice. This is classified evidence, not exact raw equality. The target still
has one missing module and five legacy/unowned paths.

CI-ONLY VERIFICATION: no new remote or after-side external-service run.
Runtime router relocation, direct persisted database parity and complete
target acceptance remain open.

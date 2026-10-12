# Amendment 19: recursive shared CE / EE target

Date: 2026-09-27. Agent-defined under Alex's instruction to define the CE tree to
its leaves and use equal physical core paths in CE and EE. **Not implementation
acceptance.** CE source: `3b844b5083e5af89269ef917bc0614601d30cf61`.

## Decision

- [Target and lifecycle](../../inner/target.md) replace the old inner target.
  [EE alignment](../../inner/edition-alignment.md) records EE ownership and exclusions.
- [Move map](../../inner/structure-review.json) reviews 479 maintained Python files
  across 73 source scopes, including namespace folders and initializer-only code.
  Nine Python files in bundled demos are excluded from this core-layout review,
  not from ArchKeel scanning or descriptor acceptance.
- Root plus 21 mounted contracts define responsibility, allowed dependencies,
  public entries and cycles. Physical rules cover the 63 already-existing target
  scopes. Newly created target scopes receive their layout rules with their move.
  Cohesive leaf folders do not need ceremonial contracts or `api.py` wrappers.
- Seven children triggers review, not automatic nesting. The explicit retained
  exceptions are Domains (9), Runtime (8), literal generators (8).
- Domain entities remain lazy property views, not invented passive DTOs. Move
  `DemographicConfig` below Demographics, not the entity layer; keep evaluation
  order and RNG draws unchanged. Setup owns Include execution. Shared count
  resolution belongs below task families, not inside Generate.
- Dissolve mixed `TaskUtil` responsibilities and Generate's empty `services/`
  wrapper. Reuse typed owner operations; do not add indirection to hide cycles.
- Alex's later no-shim decision supersedes protocol item 7 / decision D4 for
  Python module paths in 5.0. Move and document callers in the same slice. Installed
  CLI commands remain supported. This does not authorize DSL behavior changes.
- EE leads shared semantics. Compare each behavioral change to the frozen EE
  implementation before adopting it; CE replay alone is not cross-edition proof.

The frozen descriptor oracle, seeded/unseeded rules and numeric baseline remain
unchanged. `known-violations.json` has the same Git blob as HEAD:
`53f0fc6fcae5480ccc732b303ace50a8a6d3be6c`. No production Python or XML descriptor
was changed in this definition slice. EE's dirty main checkout was not edited.

## Verification and blocker

LOCAL VERIFIED:

- Definition and existing physical checks pass. The definition check verifies
  complete source review, destination collisions, active initializer preservation,
  recursive mounts, layout/map consistency and justified over-seven scopes.
- Published ArchKeel 0.8.0 parses the complete contract tree. All 22 declared
  permission graphs are acyclic. This is not an observed-import verdict.
- Independent 0.8.0 probes reject a forbidden inner edge, unexpected package and
  module cycle. Ruff and full-package MyPy pass (488 Python files for MyPy).

Full 0.8.0 observation is **UNKNOWN**: the published analyzer exceeds its fixed
60-second limit. It produces no complete new HTML report. A separate bounded
90-second `cProfile` diagnostic on the intermediate 17-contract snapshot confirms
repeated re-export index work dominates:
`_reexport_facade_entries`, 17,874 calls, 78.31 seconds cumulative and 51.45 seconds
self time. Cumulative times overlap; profiler overhead means these are not normal
wall-clock timings. The diagnostic was interrupted without a complete observation.

Reproduce the public failure with `make architecture-report`. The smallest tool
fix to investigate is one reusable re-export candidate/ambiguity index per scan;
do not loosen CE permissions, increase accepted debt or replace the public gate
with a private timeout wrapper. Baseline comparison, `--against` acceptance and
the machine-bound amendment remain pending until a full observation completes.
No amendment JSON is fabricated around an UNKNOWN result.

CI-ONLY VERIFICATION: none; not pushed in this slice. No runtime or descriptor
suite was rerun for this contract-only change. Existing behavioral gaps in the
experiment report remain open; this amendment does not turn them green.

## Follow-up: report unblocked by a local tool candidate

The fixes for ArchKeel [#192](https://github.com/rapiddweller/archkeel/issues/192)
and [#193](https://github.com/rapiddweller/archkeel/issues/193) are local candidates,
not a published release. Re-export indexes are reused per boundary pass. No
deadline, CE contract, baseline, Python source or descriptor was changed.

The [current report](../../../../test-artifacts/architecture/ce-recursive-target/architecture.report.html)
completed in 15.65 seconds on the final measured run (an earlier run: 11.46 seconds).
It observes all 488 Python modules: 529 rule violations, 18 decisive UNKNOWN
positions, 11 cycle edges. All 166 rule assessments have evaluator receipts.
This is a complete observation of an unfinished target, not architecture acceptance.

Independent browser acceptance reaches all 488 module leaves and all 21 mounted
scopes. Desktop and narrow-screen checks preserve red violations, filters and
navigation. Evidence is in `test-artifacts/architecture/ce-recursive-target/`.

Direct publication now counts a real outside caller only through every declared,
uniquely owned ancestor boundary. This removes 77 false `interface.unused`
diagnostics. Validation still reports 169 unused-entry diagnostics and one
ownership diagnostic; it remains UNKNOWN. These are not 169 proven dead APIs.
The overlapping `DemographicConfig` ownership and class-method signature coverage
need separate review before changing the target or implementing its moves.

A separate single-owner demo exposes aggregate PASS versus per-rule UNKNOWN
([#194](https://github.com/rapiddweller/archkeel/issues/194)); the current CE report
does not hit that case. ArchKeel's own call budget also blocks release of the
candidate: 562 accepted versus 567 observed unresolved calls, pending explicit
approval. No baseline was rewritten and no CI or release is claimed.

Next: finish tool acceptance, resolve the remaining contract-definition findings,
then implement the ordered target slices. Keep structural, behavioral and delivery
verdicts separate.

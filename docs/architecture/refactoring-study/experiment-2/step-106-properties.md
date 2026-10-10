# Step 106: native Runtime properties

Base `46a3f07f`; published ArchKeel **0.9.0**, Python 3.11.12.
[Amendment 98](amendment-98.md) permits a red source-annotation checkpoint.
Only SetupContext constructor/backing/getter/setter annotations changed:
`dict[str, object]`, nullable at construction. No runtime statement or caller
change; supplied dictionaries remain mutable and keep identity.

## LOCAL VERIFIED

- Independent Luna QA: RED **1 failed, 24 passed**; GREEN **25 passed**.
  Scratch mutants reject missing/narrow annotations, copying supplied maps,
  shared None defaults, setter omission, include reassignment and incorrect
  deepcopy isolation/aliasing. Independent Luna implementation owns source only.
- Full unit suite: **1,677 passed, 11 skipped, 1 xfailed**, two existing
  connection-config serializer warnings. Architecture: **1,644 passed, 14 skipped**.
  Seven definition tests, Make lint/typecheck (492 files), changed-test Ruff and
  pinned Pylint executable-cycle check pass. Independent Astra found no material
  source/test defect; an unsupported exporter rationale was corrected.
- Root independently verifies whole-file executable AST equality. All contracts,
  permissions, baseline, budgets, gates, oracle, source inventory and XML bytes
  stay frozen. Imports, dependency edges, calls, bindings, references, type
  signals, cycles and coverage are identical in the decoded observations.
- ArchKeel: **85 -> 86** violations. One raw-dict constructor finding becomes
  two explicit map/object findings; every unrelated finding is identical.
  Counted UNKNOWN stays **198**, raw records **252**. Three property annotations
  are now visible, but their effective inherited binding remains UNKNOWN;
  its aggregate record changes only those annotations. This is not resolution.
  Only the three method records, backing-property context evidence, three source
  excerpts, violation metric and source digest change besides those findings.
- Coverage: **492/492** files parsed. Report exits 0 with declared rules FAIL.
  Validation with frozen baseline and `--against 46a3f07f` exits **2**:
  baseline-new **61**, resolved **0**, nineteen `interface.usage_unknown`
  diagnostics; `delta=null`. No successful historical comparison is claimed.

## Descriptor evidence, not full acceptance

Both complete current-before/candidate captures select all **930** XML files:
383 CAPTURED, 70 EXPECTED-ERROR, 16 NOT-A-DESCRIPTOR, 77 UNRUNNABLE,
384 UNVERIFIED. All **109 captured seeded** cases compare identically; all
70 expected errors compare equivalently. Of 274 captured unseeded cases,
**258** pass the frozen comparator; **16** remain gaps (eight identical but
incomplete captures, eight differing count/presence/output-shape captures).
No flaky exclusion or comparator change was made.

The strict comparator exits **1** with 478 reported differences: unverified,
unrunnable and sixteen captured gaps, plus capabilities metadata. The latter
differs only in installed package `schema_version`, `4.3.1.dev299+dirty` versus
`4.3.1.dev300+dirty`; compiler and both reference projections are identical.
The checkout's package metadata was not a frozen version baseline. The architecture
wheel test runs `uv build` in this checkout; metadata resolves to its local
`datamimic_ce.egg-info`. Do not run that build concurrently with a projection
comparison. This is a test-orchestration gap, not a permitted oracle difference. Stable
statuses and annotation-only AST do not turn this into full DSL acceptance.
No Docker test services were running; service results remain unverified.

## Decisions and remaining work

Retain the five grouping initializers: deletion changes package semantics without
an evidenced benefit, and EE shared discovery differs. Do not invent owners or
wrappers just to silence their findings. Errors ownership remains stopped at
[#338](https://github.com/rapiddweller/archkeel/issues/338).

Root and Astra reproduce the existing nullable Authoring allowance mismatch on
released 0.9.0; [#342](https://github.com/rapiddweller/archkeel/issues/342) includes
portable positive/negative controls. No CE model/allowance workaround or ArchKeel
code edit was made. Report acceptance remains stopped at #335/#336. Full semantic
target, behavior and interactive report acceptance are **incomplete**.

The Makefile still pins 0.8.5; all measurements above explicitly use the isolated
released 0.9.0 environment. A worker's plain `archkeel` probe reached global
`0.2.1.dev37+gb105718cf`; that attempt is excluded, not a current checker blocker.

CI-ONLY VERIFICATION: no CE CI result claimed. Existing PR274 remains Draft;
conflicts and delivery readiness are separate. No merge performed.

Evidence: scratch `ce-archkeel-090-20261005.GF5VUk`, including independent
QA/implementation/Astra reports, complete captures and decoded delta assertions.

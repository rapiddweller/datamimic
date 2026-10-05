# Step 105: four existing namespace owners

Base `b55980c3`; published ArchKeel **0.9.0**, Python 3.11.12.
[Amendment 97](amendment-97.md) assigns Finance, Healthcare, Exporters and
Converters initializers to existing concerns through exact module names.
Source, exports, child selectors, public entries, requires, rules and baseline
remain unchanged. These assignments repair target ownership, not runtime code.

## Independent challenge and stop

Independent Luna implementation and QA reviewed five candidate assignments.
Astra resolved the exporter challenge: its inert marker belongs with the
common interface inside `IO -> IO-EXPORTERS -> EXPORTERS-CORE`, not IO-API.

The five-owner candidate removed exactly five findings, but validation added
`interface.unused` for the Error factory. Astra proved a checker false positive:
four consumers reach its function through the declared parent facade, yet
lifecycle validation discards those proven chains after the publisher receives
an inner owner. Root replayed the three-source-file reproducer successfully.
[ArchKeel #338](https://github.com/rapiddweller/archkeel/issues/338) records the
Errors-slice blocker. Its contract change and new test row were excluded;
no public/dependency workaround or checker fix was made here.

## LOCAL VERIFIED

- Original candidate RED: five missing exact-owner assertions fail, eleven
  tests pass. Corrected candidate: sixteen pass. After excluding Errors,
  the complete architecture suite has **1,644 passed, 14 skipped**, serial.
- Seven recursive-definition tests, Ruff source/changed-test checks, full
  MyPy for 492 files and pinned Pylint executable-cycle check pass.
- Independent installed-evaluator controls reject omitted, mistyped and
  duplicate assignments. A uniquely wrong component passes cardinality;
  literal CE tests enforce the selected design owner. This is not a checker
  defect. Root and QA each verify fifteen cold root-to-leaf export identities.
- Full decoded four-owner delta: **89 -> 85** violations; exactly four
  assignment records removed, no new finding, all retained records identical.
  Twelve scoped receipts improve to proven PASS: assignment and the newly
  unblocked interface/requires checks for each of the four scopes.
- Imports, symbols, bindings, calls, type signals, dependency edges, cycles
  and all **252 raw UNKNOWN records** are unchanged. Counted UNKNOWN stays
  **198**; coverage is PASS, **492/492 modules** read and parsed.
- Source digest remains
  `e8f6a09d77f44015e3dbb078a1cc81feedfb4d50d26585325e9ca0414c0f6b04`.
  Baseline, root contract and Makefile hashes remain unchanged.
- Released report exits 0 with declared rules **FAIL**, not target acceptance.
  Validation with the frozen baseline and `--against b55980c3` exits 2:
  baseline-new **65 -> 61**, resolved 0, and exactly the previous nineteen
  `interface.usage_unknown` diagnostics. The extra Error diagnostic is absent.
  `delta=null` means the historical comparison was not established; no
  successful widening-gate result is claimed.

The Makefile still pins 0.8.5. This slice explicitly uses the fresh released
0.9.0 environment; pin adoption remains separate. No fresh descriptor, external
service or full behavioral suite was run for this source-free correction.

## Remaining acceptance

Six initializer findings remain: Errors waits for #338; five inert grouping
roots need a namespace-packaging decision and installed-wheel/resource proof.
Typing debt and material UNKNOWN remain open. Definition checks do not prove
the physical implementation or complete semantic target has been reached.

Report acceptance is also incomplete. Independent Astra's two-source-file
fixture proves Diff omits a forbidden observed edge; root browser inspection
confirms pure Target includes actual FAIL badges and observed-presence hints.
[#335](https://github.com/rapiddweller/archkeel/issues/335) and
[#336](https://github.com/rapiddweller/archkeel/issues/336) track these report
defects. Existing JSON evidence is preserved. No ArchKeel code was changed.

CI-ONLY VERIFICATION: no CE CI result claimed. PR 274 remains Draft; its
conflicting state and delivery readiness are separate from local checks.

Scratch receipts, original five-owner evidence, revised four-owner observations,
decoded deltas and independent reports are under
`/private/tmp/ce-archkeel-090-20261005.GF5VUk/step-105/`.

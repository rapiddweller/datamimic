# Step 104: Runtime and IO namespace owners

Base `01f9a324`; published ArchKeel **0.9.0**, Python 3.11.12.
[Amendment 96](amendment-96.md) assigns two inert package initializers to
their existing API owners through exact names. No child selector, public
interface, dependency permission, source, descriptor or baseline changes.

## Release acceptance

Fresh PyPI wheel SHA-256:
`af6333eb7880dfadc5a1926dab7a48cf69ac08cc000e356e92cd07f49e1b9fbd`.
GitHub release source: `b6636e8fe874c96f165e66e0c5d7e59f386213d2`.
Independent Luna replays all eight unchanged property fixtures: typed inherited
getter/setter PASS; broad/private setter FAIL; missing annotations and uncertain
effective bindings retain source-linked UNKNOWN. Report and validate agree.
This accepts those reproductions, not every ArchKeel rule or the whole CE target.

The same CE source now exposes twelve initializer-assignment findings that
the earlier candidate missed. Those are measurement changes, not code regression.
This step resolves precisely the Runtime and IO entries; ten remain.

## Local verification

- Ownership RED: exactly two missing-owner failures, nine existing tests pass.
  After the correction: eleven pass. Existing child owners stay unchanged.
- Independent Luna evaluator controls: correct owners pass their assignment
  checks; omitted, wrong and duplicate roots fail. Checks cover 70 Runtime and
  53 IO subjects; descendants retain their owners. Astra accepts the bounded
  correction after checking these receipts and the full decoded delta.
- Full architecture suite: 1,640 passed, 14 skipped, serial, normal project plugins.
  Seven recursive-definition tests and pinned Pylint executable-cycle check pass.
- Ruff source and changed-test checks pass; full MyPy passes all 492 source files.
- Full decoded observations: exactly two assignment records removed; no new
  finding and all 89 retained findings unchanged. Imports, calls, symbols,
  bindings, dependency edges, cycles, type signals and all 252 raw UNKNOWN
  records are identical. Counted UNKNOWN remains 198.
- Source digest stays `e8f6a09d77f44015e3dbb078a1cc81feedfb4d50d26585325e9ca0414c0f6b04`.
  Baseline, root contract and Makefile hashes remain unchanged.

Both scoped assignment rules now have proven PASS receipts. Their four interface
and dependency checks also move from UNKNOWN to proven PASS: removing those
missing-owner blockers allows evaluation. Every other scope receipt is unchanged;
the counted type UNKNOWNs are not resolved by this ownership change.
Overall validation remains **FAIL**, exit 2: 89 violations, baseline-new 65,
resolved 0, and the
same 19 `interface.usage_unknown` diagnostics. Observation coverage is PASS:
492/492 modules read and parsed. No gate or baseline is weakened to hide this.

The project Makefile still pins 0.8.5; this step explicitly invokes the verified
0.9.0 environment. Pin adoption is separate from this ownership correction.
Runtime, descriptor and service suites are not rerun for this source-free step;
unchanged source is not a fresh full behavioral acceptance claim.

## Remaining acceptance

Physical-definition checks pass; semantic ownership/type completion remains open.
The generated HTML and JSON are complete observations, not target completion.
Fresh all-depth Ist/Target/Diff UI acceptance is not established. Initial browser
startup attempts failed; a later Playwright localhost run succeeds. It verifies
Target root -> Runtime -> Tasks -> Flow, view switching and Back retaining the
architecture view. The Diff legend displays `Core: unavailable`; this smoke check
does not establish complete diff evidence or all-depth usability. Packaging
decisions, full DSL/service/EE proof and delivery readiness remain separate.

CI-ONLY VERIFICATION: no CE candidate result claimed; PR 274 remains Draft.
Evidence: `/private/tmp/ce-archkeel-090-20261005.GF5VUk/step-104/` contains
RED/GREEN, full report/validation, semantic delta and independent task reports;
property controls: `/private/tmp/archkeel-090-property-qa.V69jSu/summary.md`.

# Step 90: remove empty smoke-export wrappers

Base: `25eee585`. Decision: Astra; approved bounded slice recorded in
`test-artifacts/ce-smoke-export-next-slice-astra.md` in the primary checkout.
Use published ArchKeel 0.8.4. No ArchKeel implementation work.

Goal: pass native captured rows and exporter options through the existing typed
request. Authoring owns capture/diagnostics; IO owns writing, finalization and
row counting. Do not move either responsibility.

## Global constraints

- Production scope: `authoring/adapters/dryrun.py`, `engine/io/contracts.py` and
  `engine/io/exporters/registry.py` below `datamimic_ce/`.
- Delete only SmokeExportRows/SmokeExportParameters and their imports/exports.
  Keep SmokeExportRequest; rows are `list[dict[str, object]]`, params are
  `dict[str, object]`. No replacement wrapper, shim, cast or JSON narrowing.
- Preserve payload identity, nested/native values, the shallow options copy,
  option validation, setup defaults, target precedence, worker ID 1,
  consume/finalize/count order and Authoring DM002 behavior.
- Root contract changes only IO-API-TYPES rationale/provenance and four exact
  allowed_positions: `datamimic_ce.engine.io.api.smoke_export`, position
  `request`, each field_path `rows`/`params` with each annotation
  `dict[str, object]`/`object`. No other exception or dependency/public grant.
- Update Amendment 62 with these four records and fresh measurements. No
  baseline, descriptor, comparator or historical oracle changes.
- Preserve unrelated primary dirty changes; work in the isolated checkout.
  Root owns commits/push; PR274 stays Draft. No force-push or merge.
- QA and implementation are independent Luna agents. Astra reviews the frozen
  result. ArchKeel gaps become reproducible issues only; stop if this slice
  cannot proceed safely without a checker fix.

## Task 1: independent QA

Own `tests_ce/unit_tests/test_exporter/test_smoke_export.py` and
`tests_ce/architecture/test_io_public_boundaries.py`; extend existing Authoring
tests only for a genuinely missing behavior. No production/contract edits.
Read the real caller, request and registry before testing. Show RED against
the committed base for native annotations/payloads; keep existing byte-output
assertions and all unrelated tests.

Cover native/nested opaque identity and shallow parameter copying through the
real registry. Check chunk_size/encoding rejection, unknown exporter, consume
and finalization failures, ordered finalization/counting. Reuse unchanged
Authoring tests for defaults, output dialects, no leaked files, unserializable
values and short writes. Do not replace that coverage with mocked successes.
Use real released-checker negative probes: another method/field, misspelled
field path and a fixed control must not inherit the four allowances.
Record precise commands, RED/GREEN outcomes and limits; no worker commit/push.

## Task 2: implementation

Own only the three production modules and root IO-API-TYPES hunk. Wait for
independent RED. Replace wrapper construction/access with direct payloads;
delete empty classes/import/exports. Keep every other branch unchanged.
Add the exact four contract records above, without importing the dirty root
contract. No test edits. Read all callers before changing types.
Run focused tests, standard definition checks, make lint and make typecheck.
Record commands and results; no worker commit/push.

## Task 3: root acceptance and checkpoint

Capture released-checker snapshots for base, source-only removal, and source
plus exact amendment. Record findings/UNKNOWNs; do not reuse old counts.
Run the full unit suite, affected Authoring/exporter tests and unchanged
descriptor/projection oracle before versus after. Seeded values compare within
CE; unseeded structure compares without pretending random values are stable.
Full corpus/service acceptance stays unfinished unless actually run.

Astra independently reviews the bounded diff and evidence. Generate the exact
digest-bound amendment, update the step report, and commit/push only this slice.
Regenerate CE HTML/JSON. No PASS claim for UNKNOWN or outstanding global FAIL.

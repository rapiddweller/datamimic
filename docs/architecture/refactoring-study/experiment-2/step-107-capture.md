# Step 107: native capture rows

Base `26e01b15`; published ArchKeel **0.9.0**, project Python 3.11.
[Amendment 99](amendment-99.md) permits this bounded red source checkpoint.
IO storage and Runtime/Python capture surfaces now describe the actual
`dict[str, list[object]]` result, with existing optionality. Values, order,
counts, references and both explicit/lazy capture streams stay unchanged.

Factory overlays, including `{}`, now require dictionary rows and raise
`TypeError("Factory custom_data requires dictionary rows")` otherwise.
This deliberately rejects previously supported non-dictionary objects with
`update`; no-overlay native results remain supported. Assertions run first;
subclass update overrides/errors and partial batch mutation remain. No EE parity
or external-caller compatibility claim.

## LOCAL VERIFIED

- Independent Luna QA: **18 failed / 58 passed RED**, then **76 passed GREEN**.
  All **16** in-memory mutants killed; root reran the same harness. They cover
  each public annotation separately, capture copying/stream loss, both guards,
  empty overlays, assertion order, batch prevalidation and subclass dispatch.
  Factory native-row rejection uses boundary doubles; real XML separately
  proves capture contents/order and count-assertion precedence.
- Independent Luna implementation changes six source files. Root's executable
  AST proof admits five annotation-only files and exactly two approved factory
  guards plus one local binding. Source inventory, XML, policy, allowances,
  baseline, budgets, Makefile and oracle remain unchanged. Astra approves source
  scope, not final architecture/DSL acceptance.
- Full units: **1,708 passed, 11 skipped, 1 xfailed**, two existing connection
  serializer warnings. Architecture tests: **1,644 passed, 14 skipped**.
  Seven recursive-definition tests, Make lint/typecheck (492 files), changed-test
  Ruff and pinned Pylint executable-import-cycle check pass. ArchKeel still
  retains its existing two package/type-cycle edges; no all-cycle-free claim.
- Normal-import MyPy probe confirms `object` rows before the factory guard and
  `dict[Any, Any]` afterward. The guard does not establish dictionary field types.

## Machine report remains red

Violations **86 -> 87**: two IO getter findings now describe native map/object
rows; one new `runtime.api.run` / `return.captured` map finding is outside the
frozen dictionary-row allowance. Counted UNKNOWN **198**, raw UNKNOWN **252**.
No new permission or baseline entry hides it.

The complete decoded comparison preserves imports, dependencies, ownership,
contracts, references and cycles. Factory calls/evidence change with the guards;
unresolved calls **1,234 -> 1,233** is only a recorder change. The dictionary
update still has heuristic, partially resolved candidates, not proven dispatch.
All **492/492** source files parse; report exits 0 with declared rules FAIL.
Frozen-baseline validation against the base exits **2**, baseline-new **62**,
resolved **0**, 19 `interface.usage_unknown` diagnostics and `delta=null`.
No successful checker historical comparison is claimed.

## Descriptor evidence, not full acceptance

Both serial runs select all **930** XML files: 383 CAPTURED, 70 EXPECTED-ERROR,
16 NOT-A-DESCRIPTOR, 77 UNRUNNABLE and 384 UNVERIFIED. All **109 captured seeded**
results and **70 expected errors** compare identically/equivalently. Of 274
captured unseeded cases, **258** pass; **16** remain gaps: eight identical but
incomplete captures and eight differing count/presence/output-shape captures.
The unchanged strict comparator exits **1** with **477** differences. Equal
incomplete evidence does not pass. No descriptor or comparator was relaxed.

Capabilities, compiler and both reference projections are byte-identical between
these two runs. Package version/path/metadata bytes were frozen at
`4.3.1.dev300+dirty`; the architecture wheel test ran only afterward. This is
current-slice proof, not original Step-0 final proof. The historical capability
oracle still differs. Docker has no running services; DB-backed results remain
unverified, and the frozen recorder skips its external-service category.

## Remaining work

- Physical definition checks pass; semantic convergence and final target do not.
  Errors ownership remains stopped at ArchKeel #338, nullable Authoring allowance
  matching at #342. Pure Target/Diff/deep navigation acceptance remains incomplete
  at #335/#336/#340; no fresh browser acceptance is claimed.
- Real Authoring raw-XML smoke control stays mapping-only. Its pre-existing mixed
  internal-row filtering/completeness mismatch stays unchanged and is tracked as
  [CE #285](https://github.com/rapiddweller/datamimic/issues/285), public reachability
  unproved. No Authoring source changed.
- The report labels the total as “Forbidden symbol crossings” although the base
  has 80 type and six assignment findings, no forbidden-symbol finding. Tracked
  as [ArchKeel #349](https://github.com/rapiddweller/archkeel/issues/349); no ArchKeel
  implementation here. Make still pins 0.8.5; measurements explicitly use 0.9.0.

CI-ONLY VERIFICATION: no result claimed. Existing PR274 remains Draft; conflicts,
remote CI and final delivery acceptance are separate. No merge performed.

Evidence: scratch `ce-archkeel-090-20261005.GF5VUk`; before/after full captures,
decoded report delta, AST/provenance assertions and independent reviews.

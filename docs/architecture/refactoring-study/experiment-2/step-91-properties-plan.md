# Step 91: native Runtime properties

Base: `3f604a3b`; published ArchKeel 0.8.4. Astra approves the bounded
properties slice and canonical top-level selector. No ArchKeel edits.

Interfaces adapt input; Runtime owns sequencing; DSL owns property syntax and
credential merging. Pass the same native property map through the existing
RunRequest. Remove packaging, not behavior or validation used by this flow.

## Scope

- `engine/runtime/contracts.py`: delete only PlatformProperties. RunRequest's
  platform_props becomes `dict[str, str] | None`. Keep PlatformConfiguration.
- `engine/runtime/api.py`: remove the wrapper import/construction; return the
  parser's `dict[str, str]` directly. Preserve lookup and missing-file handling.
- `interfaces/python/datamimic.py`: pass the caller map directly, preserving
  None and identity. No new validation, copying or coercion.
- `engine/runtime/lifecycle/runner.py`: use request.platform_props directly,
  passing that same object to DescriptorParser and SetupTask.

Paths are below `datamimic_ce/`. No shim, replacement wrapper, cast, parser,
configuration, descriptor or Step-90 change. External wrapper consumers remain
UNKNOWN; this is an approved internal Python API contraction for CE 5.0.

Root owns only RUNTIME-API-TYPES rationale/provenance and Amendment 89. Preserve
the existing capture allowances. Add exactly these property permissions below
`datamimic_ce.engine.runtime.api`:

| Qualified name | Position | field_path | Annotation |
|---|---|---|---|
| load_descriptor_properties | return | empty string | dict[str, str] |
| create_run_session | request | platform_props | dict[str, str] |
| run | request | platform_props | dict[str, str] |

The original advisor's word "absent" was a plan-format error: released schema
requires field_path. Astra approved the documented empty-string selector for
the same top-level return. No scope expansion or checker workaround is intended.

## Independent tasks

1. Luna QA first runs published-checker preflight in a disposable copy. Exact
   positive, wrong field path, unrelated fixed request map and changed loader
   return annotation must show the intended restrictions. An external Path
   must not hide sibling findings. Stop if this cannot be proved; issue only,
   never an ArchKeel implementation or broader exception.
2. QA owns `tests_ce/unit_tests/test_python_api/test_runtime_boundary.py`: RED
   for native loader/request annotations and wrapper removal, then preserve
   existing direct value/identity checks, caller's non-string marker, missing
   file and CLI properties behavior. Add one parameterized real-lifecycle check
   for None/empty/populated maps at parser and SetupTask arguments. Keep real
   execution tests; do not replace them with mocked successes. Preserve the
   run.captured permission assertion when adding a separate request permission.
3. Independent Luna implementation waits for RED, owns only the four production
   paths above, reads all callers and makes the minimal change. No test/contract
   edits. Root applies exact contract permissions after preflight approval.
4. Root runs affected Python/CLI and unchanged DSL property checks, full Make
   unit suite, definition/cycle/lint/type checks and unchanged before/after
   descriptor/projection oracle. Selected proofs do not certify the full corpus.
   Root retains source-only versus exact-amended checker captures and creates
   the digest-bound amendment without changing the accepted baseline.
5. Astra reviews specification and code quality independently. Root finalizes
   evidence, commits/pushes only the slice to the existing experiment branch,
   keeps PR274 Draft and regenerates separate commit/IDE HTML and JSON reports.

No gate, skip, xfail, oracle, descriptor or baseline weakening. Preserve unrelated
primary changes. No force-push, merge or ArchKeel release. Global FAIL/UNKNOWN and
full semantic/report/behavior acceptance remain open unless actually verified.

# CE 5 authoring and plugin review

Independent follow-up from `771c25a6f5b0f75438cfc18a03cc26195b1d0f65` for
setup #344, workspace snapshot #345 and the human-first steering in #337.
The earlier corrected-diff review covered #333 and #337–#343.

## Current findings

No remaining source or setup blocker found in this diff. Setup reuses the selected project environment,
respects explicit pins, installs published CE 5 only when needed and verifies the
live contract. Both plugin manifests use version 0.2.0; Codex onboarding resolves
to the packaged setup skill. Existing Platform service use needs no local install. The release and docs-index
wording consistently names shared setup/authoring and links the complex-reference gate.

The production change excludes root `.venv`/`venv` directories after the
non-following stat and before traversal. Nested data directories retain their
contents. Model-resource symlink refusal, opened-file identity checks, replacement
race checks and size/count/depth limits remain in the existing shared snapshot
path. The regression covers an original project root containing a Python symlink
inside its environment and a relative CSV resource. No workspace narrowing is
needed or accepted as proof of this fix.

The shared authoring/review guidance keeps native field operations and rule
parameters visible, requires justified typed Python with explicit inputs/outputs,
and distinguishes exhausted search from infeasibility. Normal runtime remains
separate from bounded approval: inline and file helpers compile/roundtrip and
execute, but Build still rejects their unsupported operation before loading them.
No policy or trusted-execution boundary was expanded.

The [complex reference evaluation](../../../evaluations/complex-authoring-reference.md) preserves the original
11-table/27-column, 540-row task and positive/negative R1–R6 controls. It is a
reference gate, not completed CE acceptance. Planning-before-cleanup does not
prove atomic cleanup/export. The full CE gate remains open under #332/#270.

## Architecture

Fresh native observation parses 534/534 files: zero violations, 271 rules PASS,
5 UNKNOWN, 1425 unresolved calls, 178 typing positions, 2 cycle edges and zero
private crossings. All 303 raw UNKNOWN records and all 20 validation diagnostics
match the previous receipt, including the raw UNKNOWN digest. Classifications,
contract, analyzer and approved ceilings remain unchanged.

[The receipt](completion-unknowns.json) binds source digest
`198f3c582b683d172af8284228ba49ce9bbe06faa997919ff478687f1ec0e66e` and the fresh
validation to that unchanged uncertainty. It does not certify complete resolution
of inherited surfaces, external/generic types, reexport routes or dynamic contexts.

## Evidence boundary

Reviewer independently ran 38 bounded-executor, plugin metadata and typed-Python
normal-runtime tests: all passed. Only the retry plugin and cache provider were
disabled; the retry plugin's localhost socket is unavailable in the sandbox.
The four Python cases verify inline/file function visibility, one load per run,
exact JSON/readback/replay, negative no-output and retained bounded rejection.

Inspected `/private/tmp/datamimic-ce5-human-first/` logs: `full-unit.log` reports
3003 passed/15 skipped; `workspace-green.log` 66 passed/4 Windows skips;
`lint-type.log` Ruff and MyPy pass on 534 files. `installed-base.log` and
`installed-mcp.log` show successful isolated 5.0.0 real-child checks, 13 schemas,
and 0/11 MCP tools. These are locally built candidate-wheel results.

The fresh installed-wheel `final-scenarios/summary.json` and
`complex-scenarios.log` report four Ready cases. Raw receipts, XML hashes and
verification results match that summary. Memstore full tuple/readback and
relational/embedded Person/Address oracle results pass; the latter two also pass
requested smoke/replay. SQLite reports actual 6/12/24-row delivery and rejection
of an invalid composite child. Reviewer independently checked those database
counts and an empty foreign-key integrity result. These cases do not satisfy
the separate full complex-reference gate.

The fresh Luna original-root controlled-index evaluation produces two Ready
Builds from the root containing `.venv` and relative CSV data. The reviewer reran
its independent assertions and installed CLI Build at that exact root: all three
source pairs, generated names, XML and full replay match. The environment freeze
and configuration hashes are unchanged. The independent raw response is
`/private/tmp/datamimic-ce5-human-first/reviewer-root-proof.json`.

That original-root attempt confirms the snapshot fix but failed setup reuse:
it unnecessarily invoked pip despite a compatible CLI, and the two rejected Build
responses are missing despite the original report claiming retention. Exact
source-field preservation is independently asserted; the final Build certifies
count, not the removed source-inferred-field uniqueness expectations.

The corrected setup skill makes compatible discovery terminal. A fresh
setup-only retest in `/private/tmp/datamimic-ce5-human-first/reuse-retest/` uses
that exact skill and confirms CE 5/Build 4.0 without install, upgrade or dependency
writes. Its 56-package inventories and project-root hashes match before/after.
Read-only `pip list` was used for evaluator inventories; two initial unquoted-path
errors were corrected and retained. The earlier failed reuse attempt and missing
rejected responses remain limitations of that attempt, not erased by this retest.
The earlier child-workspace workaround is not acceptance evidence.

Public PyPI CE 5 setup remains unavailable; a controlled-index run cannot
establish public installation.
Native Claude testing is explicitly deferred; native Codex remains blocked by
model configuration. Neither host has proven the complete workflow.

LOCAL VERIFIED: source/caller/security review, 38 independent tests, fresh native
identity/uncertainty assessment, installed original-root Build/replay and the
inspected local logs above.
CI-ONLY VERIFICATION: current-delta CI and native Windows remain unverified here.
No public installation, full complex-reference acceptance, merge or release approval is implied.

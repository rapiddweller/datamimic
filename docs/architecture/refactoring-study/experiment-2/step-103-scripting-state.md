# Step 103: native Python scripting state

Base `7d6fb7fd`; published ArchKeel 0.8.5. Delegated Astra's
[Amendment 95](amendment-95.md) corrects the fixed-model demand at 12 native
Python-state/copy-memo positions. Root added exactly 22 permissions and their
provenance; the nine existing Runtime permissions remain unchanged.
No product, XML, ownership, public export, baseline, budget, oracle or gate edits.
This is a target correction, not 22 source fixes or proof of type closure.

LOCAL VERIFIED: independent Luna QA's new exact permission test fails before
the contract edit (whole file: 1 failed/31 passed), then passes (32 passed).
Context tests: 60 passed. Inline execute/dynamic include: 9 passed. Full units:
1,671 passed, 11 skipped, one existing xfail, two existing Pydantic warnings.
The include/Ray unit path remains skipped; passing integration is not unit proof.
Root reran the context, expression, converter, execute and Runtime boundary
files together: 71 passed with normal pytest plugins. Ruff/full MyPy 492 files,
pinned executable Pylint, seven recursive-definition and four physical checks pass.

Astra caught missing proof for scripted classes/instances and non-Converter
results. One two-case test now executes a real script, preserves native class
and instance identity, reads its value and rejects both converter forms.
Independent Luna's full unit rerun and Astra's scoped re-review accept this
bounded checkpoint. No product fix was needed for the existing guards.

Root's complete decoded comparison removes exactly 22 selected Runtime
findings and adds exactly 22 permission FACTs. Twelve explicitly disclose
accepted opacity with type closure unproven. All 80 retained findings and
188 raw UNKNOWN records are byte-equivalent. Source digest, imports, paths,
calls, cycles, modules, ownership and scope receipts are identical. Only the
reviewed rule/declaration, allowance signals and resulting metrics change.
Independent published-checker probes retain findings for wrong names,
positions, field paths, annotations and depths, plus bare/wrong-key/deeper
maps, extra union branches, duplicate map occurrences and unrelated config.
Shape mutations carry the original permissions at the same name/position;
a real depth-2 permission still rejects a depth-1 opaque value. Root reran
the fixture: complete scan coverage, exact positive FACT pair and all eleven
negative seams still failing. The checker's plugin-disabled runtime subset
is supplemental only, not project acceptance evidence.

Strict architecture gate remains FAIL: 102 to 80 violations, counted UNKNOWN
134 unchanged; baseline-new 64 to 56, resolved 0. Properties, mixed generator
cache, source-length and demographic debt remain visible. No blanket waiver.
Full 930-descriptor/service/EE proof, coverage and all-depth report acceptance
remain open. ArchKeel 263's fix is merged after the installed 0.8.5 release;
closure alone does not prove this release's nested Diff behavior.

CI-ONLY VERIFICATION: no candidate CI result claimed. Existing PR stays Draft.
Evidence: `/private/tmp/ce-step103-qa-fix-report.md`,
`/private/tmp/ce-step103-checker-report.md`,
`/private/tmp/ce-step103-scoped-review.md` and primary `test-artifacts/step-103-*`
observations, strict gate and decoded semantic receipt. No full completion claim.

# CE 5 authoring and plugin review

Independent corrected-diff review from
`139c52bebae088326685399a10fd3c6b2c7684a9`, covering issues #333 and #337–#343.
This follows the earlier MCP workspace/plugin review from `8f89cd4`.

## Findings resolved

- The worker uses Python `-P` to prevent launcher-directory package shadowing;
  explicit development `PYTHONPATH` remains supported. Crash evidence includes
  the numeric return code without exposing child stderr.
- Live typed metadata describes role scope and the closed row-condition grammar.
  The incorrect `this.field` claim was removed. Field-owned examples survive
  schema projection without a second DSL catalog.
- Scalar weighted variables use the existing sampler and seeded RNG. IO counts
  their native weighted pool rather than sending it to the dictionary-row reader.
  Casting and scripted contents remain in the existing variable task. Unsupported
  unique/storage/non-random options reject explicitly; weighted-entity behavior
  remains unchanged. Typed source metadata now explains these distinctions.
- The added `setdefault` call was replaced by a guarded dictionary assignment,
  preserving existing annotation examples without adding an unresolved call.
- The shared skill uses live discovery and requires a human review with complete
  keys, counts, destinations and requirement-to-evidence mapping. Consumer docs
  describe the requested released PyPI workflow; this is not publication evidence.

Issue #343 corrects the cold registry test to the current authoring CLI, compact
capability index and typed invalid-child diagnostic. It retains positive and
negative cases in a foreign working directory; no production behavior changes.
The startup/stdio/SSE log reports seven passing checks.

No remaining blocker found in this corrected diff. The earlier startup-dotenv
mock defect was fixed and verified before this follow-up.

## Architecture

Fresh native observation parses 534/534 files: zero violations, 271 rules PASS,
5 UNKNOWN, 1425 unresolved calls, 178 typing positions, 2 cycle edges and zero
private crossings. All 303 UNKNOWN identities retain their prior classifications;
all 20 validation diagnostics match the previous receipt. The raw UNKNOWN digest
changed and was reviewed/rebound; records are not claimed byte-identical.

The contract digest changed solely for rationale/responsibility wording. Parsed
contracts excluding those prose fields match the base. Rules, approved ceilings
and analyzer are unchanged. [The receipt](completion-unknowns.json) binds the
current source, contract, analyzer, validation and UNKNOWN records. Residual
inherited surfaces, external/generic types, reexport routes and dynamic/context
resolution remain UNKNOWN; this review does not certify complete resolution.

## Evidence boundary

Reviewer independently ran weighted-variable and reference tests: 25 passed.
Inspected `/private/tmp/datamimic-ce5-luna/` logs: `full-unit-final.log` reports
2999 passed/15 skipped; `weighted-final.log` 149 passed; `weighted-length-green.log`
41 passed; `lint-typecheck-final.log` Ruff and MyPy pass on 534 files. Isolated
installed base and MCP logs show real-child success (13 schemas, respectively
0/11 MCP tools) from the locally built 5.0.0 candidate. This is not a PyPI release.

The four final-wheel scenarios in `final-scenarios/summary.json` return Ready.
Their raw receipts and oracle outputs cover Memstore tuple/readback preservation,
relational and embedded Person/Address data, and requested smoke/replay. SQLite
real execution writes 6/12/24 rows; the rerun script checks complete composite
joins, uniqueness, per-parent counts, foreign-key integrity and a rejected invalid
child insert. `package-readback.log` and its checked script establish byte equality
for 1723 tracked package files in both wheel and sdist, plus the packaged plugin
review reference. These are final local artifact results, not public installation.
Claude native testing is explicitly deferred. Codex native execution remains
blocked by model configuration. Neither host has proven the complete workflow.

LOCAL VERIFIED: corrected source/caller review, 25 independent tests, native
identity/uncertainty assessment and the inspected logs above.
CI-ONLY VERIFICATION: exact-head CI and platform matrix remain unverified here.
No public installation, merge or release approval is implied.

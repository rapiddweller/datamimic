# Amendment 174 — exact DSL alias map

2026-10-09. Base `1226d501bf0f821e98c2d647316aadc9daf98d86`.

Allow only `datamimic_ce.engine.dsl.api.element_aliases` at `return`, empty
`field_path`, exact annotation `dict[str, str]` in `DSL-API-TYPES`.
The owned registry constructs a fresh alias-to-canonical snapshot; built-in and
extension-defined keys are vocabulary data. Authoring reference and capabilities
consume that map. A fixed DTO or wrapper would change this existing API.

Retain all 17 prior allowances and every other restriction, grant, owner and
source/test/baseline byte. [Amendment 77](amendment-77.md) and
[Amendment 91](amendment-91.md) supply precedent, not an automatic exemption.
Only the amended rule changes `decided_by` from architect to agent: attribution
is rule-wide because the schema has no per-entry label. This records the new
delegated exception without representing it as human confirmation or revoking
retained policy.

LOCAL VERIFIED: source/caller/test inspection; pinned matcher has one exact match
and seven nonmatches; definition 13 PASS, full Ruff/MyPy PASS (488 source files).
Fresh report has complete observation/coverage and global FAIL87 / 200 measured
UNKNOWN / 254 canonical UNKNOWN. Only `VIO-3a3fd6bc7834db21` disappears; all 87
remaining violations and all UNKNOWN records match the prior report exactly.
One allowance fact is added; eight retained allowance facts change only shared
rule provenance. Owners, dependency permissions and source/test/baseline bytes stay unchanged.
Full projection retains 151 components, 25 contract levels and zero ownership gaps.
The recorded MODEL-REGISTRY filter has zero findings while preserving global FAIL;
it does not verify the current tree or complete semantic responsibility review.

Baseline validation exits 2: 56 new, zero resolved, 19 diagnostics/59 failures.
Unamended against-base exits 2: 19 diagnostics/61 failures and two widenings for
`DSL-API-TYPES` (`allowed_positions`, `decided_by`); amendment status is null.
Machine binding remains OPEN/#415. These results are retained, not waived.
CI-ONLY VERIFICATION: no new-head claim. Exact-base push/PR CI each completed with
24 successful jobs, two architecture failures and two skips. Their contract logs
contain no native result packet; that job's native cause remains UNKNOWN.
External consumers, mistyped extension validation and full DSL/whole-target
semantic acceptance remain UNKNOWN. No native or installed-wheel rerun.

# Existing API decisions implementation plan

> Workers use subagent-driven-development. Root owns commits; QA and implementation stay independent.

Goal: replace omitted public decisions with the existing deliberate interfaces.
Architecture: keep the same source and physical owners; assign the Authoring
initializer exactly to its API owner. No new facade or compatibility shim.
Stack: existing JSON contracts, pytest, published ArchKeel 0.8.4.
Spec: [Amendment 88](amendment-88.md). Base: `0b0dc64b`.

## Global Constraints

- ArchKeel is published `archkeel==0.8.4`; source and baseline stay byte-identical.
- No production, descriptor, oracle, physical move, dependency permission or rule change.
- Only deliberate internal API entries; external declarations stay unchanged.
  No recursive namespace, helper or new source export.
- Keep existing public entries and all task owners except the already decided initializer.
- Authoring initializer is the only new exact owner; siblings and descendants stay fixed.
- Independent Luna QA and implementation, Astra review; root stages and commits.
- Preserve primary dirty work; CE PR274 stays Draft; no force-push or merge.

## Review Focus

- Omitted `public` is not `[]`: all three missing decisions must be explicit.
- The two consumed use-case APIs must not be hidden behind empty public lists.
- Keep canonical package aliases unchanged; external type closure remains pending.
- Exact initializer ownership must not absorb sibling modules or descendant policies.
- Permitted APIs must not silently exempt helpers or boundary-type uncertainty.

## Task 1: independent QA

Own only `tests_ce/architecture/test_public_api_contract_ownership.py` and QA artifacts.
Reuse its loaders. Add `test_existing_entrypoints_have_explicit_inner_public_decisions`
with hand-written expected public lists and exact initializer ownership. Demonstrate
RED before contract implementation. Keep existing tests and assertions unchanged.

Expected decisions:
- TASKS-REGISTRY: `public: []` (field present).
- SHARED-USE-CASES, prefix `datamimic_ce.domains.shared.use_cases`: exactly
  `address_api:AddressRequest`, `address_api:generate`, `person_api:PersonRequest`,
  `person_api:generate`, each fully qualified.
- HEALTHCARE-USE-CASES, prefix `datamimic_ce.domains.healthcare.use_cases`: exactly
  `doctor_api:DoctorRequest`, `doctor_api:generate`, `patient_api:PatientRequest`,
  `patient_api:generate`, each fully qualified.
- AUTHORING-API: retain package selector/public `datamimic_ce.authoring.api`, add
  exact module `datamimic_ce.authoring`. Preserve COMP-AUTHORING's three internal
  public entries and the five existing external declarations. Do not add aliases
  or exposed model types. Existing transport tests protect the canonical exports.
  Test the changed inner decisions; compare unchanged external declarations against
  the frozen base in the independent checker evidence.

Run existing Authoring transport and domain-facade tests unchanged. Compare released
checker before/after observations on unchanged source. Check actual owner delta,
alias origins, rule receipts, violations/UNKNOWN signatures, and target visibility.
In disposable copies, probe a same-prefix sibling and non-public helper import;
use the real checker, not a test-local resolver. Report absent evaluator proof as
UNKNOWN. Write command/output/hash evidence and any limits to task-1-report.md.

## Task 2: implement the contract decisions

Own Makefile and these contracts only:
`architecture-contract.json`, `docs/architecture/inner/authoring/architecture-contract.json`,
`docs/architecture/inner/runtime/tasks/architecture-contract.json`,
`docs/architecture/inner/domains/shared/architecture-contract.json`,
`docs/architecture/inner/domains/healthcare/architecture-contract.json`.
Read the actual initializer, four use-case modules and facade consumers first.
Wait for independent RED. Apply Task 1's exact decision values, with no other
contract hunk. Add only the new stdlib-only test node to the existing
`architecture-definition-check` target. Do not create another gate or dependency.
Run standard definition checks and relevant existing tests. No worker commit/push.

Astra's final correction is recorded in Amendment 88 and
`.superpowers/sdd/step-89-public-decisions-plan/public-model-export-decision.md`.
Retain the first placement's ten unused-entry errors and the external attempt's
twelve missing types / ten literal-export errors. Remove those attempted external
additions; keep source unchanged. External API completion is explicitly deferred,
not silently accepted on the strength of definition tests.

## Task 3: review and checkpoint

Root compares all unchanged source/baseline bytes, captures same-checker evidence,
and records a digest-bound amendment without accepting baseline debt. Astra reviews
spec and quality against a bounded diff package. Stage only this step, commit and
push to the experiment branch; regenerate full CE HTML/JSON. Keep global acceptance
FAIL/UNKNOWN until proven otherwise. Then implement the approved smoke-export slice.

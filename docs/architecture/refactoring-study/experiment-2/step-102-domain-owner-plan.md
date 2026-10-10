# Step 102: Domain namespace ownership

Base `fe155c07`; published ArchKeel 0.8.5. Astra's reviewed decision:
assign the inert `datamimic_ce.domains` initializer to existing DOMAINS-API.
The inner target already declares its responsibility but omits its owner.
This prevents complete interface/requires receipts. Do not change the checker
or delete the docstring to make the marker invisible.

## Task 1: independent QA

Independent Luna QA owns only
`tests_ce/architecture/test_public_api_contract_ownership.py`: add one focused
assertion for exact initializer ownership, unchanged API package selector and
unique ownership. Observe RED before the contract edit. Run the whole existing
ownership file before/after and broader architecture tests afterwards. Normal
pytest plugins; no source, contract, docs, Git or agent writes. Report exact
results to this plan's ignored task-1-report.md.

## Task 2: independent implementation inspection

Luna's independent producer/consumer and selector inspection is read-only on
the contract. Review initializer source, selectors, explicit nested owners
and similar existing exact-module assignments. Propose the smallest JSON
diff, guard against package-selector widening or a duplicate owner, and
report concerns to this plan's ignored task-2-report.md. No source, test,
contract, docs, Git or agent writes. Root applies the reviewed JSON decision,
writes the amendment/report and owns Git after QA RED.

Add only `exact_modules: ["datamimic_ce.domains"]` to DOMAINS-API and state its
namespace-marker responsibility. Preserve packages/public/requires/rules and
all other owners. No source, XML, baseline, budget, allowance, oracle or gate
edits; no broad domains package selector, new owner or wrapper.

Root verifies the unchanged source/import/cycle/type evidence with fresh
decoded observations. The two Domain interface/requires assessments must
have complete evaluator receipts, not merely zero observed violations.
Run ownership/recursive/physical architecture tests and the strict gate;
retain existing FAIL/UNKNOWN. Source bytes, inventory and four projections
must remain unchanged. Fresh independent Astra reviews before checkpoint.
Full DSL/service/EE proof and report acceptance remain separately open.

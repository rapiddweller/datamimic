# Step 101: setup state and copy boundary

Base `37c7510d`; published ArchKeel 0.8.5. Astra chose the dynamic namespace/
global-state and copy transaction as one batch; independent Luna agents
implemented source and tests. [Plan](step-101-setup-state-plan.md).
[Amendment 93](amendment-93.md) records Astra's exact red-checkpoint decision;
the per-step count-decrease gate is not satisfied.

SetupContext now declares its real dictionary/object state and shared-copy
contract. Arbitrary Python classes, clients and objects remain supported.
The typed Memstore accessor exposed nullable DSL `cyclic` reaching IO's bool
contract. Runtime now supplies `bool(stmt.cyclic)`, matching sibling routes:
None/False remain finite; True retains wrap-around and isolated row copies.
No wrappers, allowances, baseline, budget, gate, oracle or XML edits.
Context's executable AST is identical after stripping annotations; only the
source-routing bool default adds executable behavior.

LOCAL VERIFIED: corrected test-first runs failed only on one missing context
signature and then on the omitted cyclic flag. Two invalid test assumptions
were corrected before production edits, not used to justify code changes.
Final root context/source tests: 61 passed. Independent units: 1,668 passed,
11 skipped, one existing xfail; two existing Pydantic warnings remain.
Functional: 133 passed; integration: 571 passed/2 skipped;
API/factory: 393 passed/1 skipped. Ruff and full MyPy (492 files) pass.
Independent Astra review: spec and code/test quality PASS for this bounded
slice, including Amendment 93; no remaining blocking findings.

Decoded observation: 93 -> 102 violation records; 141 -> 134 counted UNKNOWN,
195 -> 188 raw UNKNOWN. Exactly seven missing annotations disappear. Runtime's
summary becomes 114/129 decided (was 107); missing annotations 11 -> 4. Twelve
map/object findings are added and three raw-dict findings replaced. This is
more explicit type debt, not an architectural improvement claimed from counts.
Contract, imports, edges, transitive paths, cycles, packages and modules are
identical. The sole extra call is resolved `bool`; coverage remains 492/492.

Pinned executable-cycle, seven recursive-definition and four physical-target
checks pass. The unchanged strict architecture gate remains FAIL:
baseline-new 64, resolved 0. Properties and mixed generator-cache debt remain.

Thirteen bounded descriptors ran before/after. Nine have sufficient unchanged
capture evidence; four nested-list cases remain UNVERIFIED. The unchanged
strict comparator rejects those four incomplete captures. Inventory 930 and
four Authoring projections are identical. Full descriptor/service/EE parity,
90% coverage and all-depth report acceptance remain open; nested Diff is
tracked by ArchKeel #263. Domain initializer ownership is the next separate
contract step, not an ArchKeel workaround.

CI-ONLY VERIFICATION: no result claimed for this uncommitted candidate.
Evidence: ignored SDD task reports and primary `test-artifacts/step-101-*`
logs, captures, observations and decoded semantic receipt.

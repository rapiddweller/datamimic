# Step 96: raw DSL validation boundary

Base `bd19d370`. Astra approved this boundary after tracing runtime parsing
and Authoring lint. Raw attributes are an open dictionary; constraint facts
are closed types. Both routes retain one validation implementation.

## Task 1: Independent tests

Own only the existing model constraint/count and Authoring constraint tests.
Challenge the four public validators before implementation. Add only missing
checks for dictionary/nested identity, failure without mutation, ordered first
error, lazy suppliers, bool gates and temporary count coercion. Distinguish
already-passing preservation checks from a genuine failing typed-boundary check.
Use real validators/models/lint. No production, contract, descriptor, oracle,
gate or Git edits. Record RED and compatibility results separately.

## Task 2: Independent implementation

Own `datamimic_ce/engine/dsl/model/validation.py` and
`datamimic_ce/authoring/domain/rules/semantic_rules.py` only.
The four shared `check_constraints`, `check_exist_count`,
`check_weights_require_values` and `check_min_max_count` operations take and
return `dict[str, object]`. Type their existing read-only helper inputs and
the Authoring callbacks consistently. Contextually type the existing XML
attribute dictionary. Correct directly affected delegates only if necessary.

Preserve input identity, order, messages, causes, coercion timing and runtime
behavior. Do not add a DTO, wrapper, alias, cast, reflection, new normalization,
extra copy, TypeVar, dependency or broader ModelUtil cleanup.

## Root acceptance

Freeze unchanged seeded/count/weight/unique descriptors and four Authoring
projections before production edits. Independently review source-only checker
evidence before adding Am91: exactly the four facade operations' `values` and
`return` positions, admitting only `dict[str, object]` and nested `object`.
Removing an allowance or changing its position/type must remain detectable.
No baseline/budget/gate changes; never suppress constraint-supplier UNKNOWN.

Run independent checks, relevant model/parser/Authoring suites, unchanged
descriptors/projections, Make units, lint/full MyPy, recursive definitions,
pinned Pylint and published ArchKeel 0.8.5. Expect eight old findings resolved,
but accept only measured evidence. Fresh Astra review precedes scoped commit
and push to Draft PR274. Primary dirty drafts remain untouched.

No physical completion or whole-goal PASS is implied. External static Python
callers with narrower invariant dictionaries may need their annotation updated.
Memstore ownership, full parity, coverage, EE and report acceptance remain open.
No ArchKeel implementation was needed; the 0.8.4 checker blocker stopped the
earlier checkpoint.

## Historical status: blocked on ArchKeel 0.8.4

The Task 1–2 checkpoint was blocked by the published ArchKeel 0.8.4 selector
limit. At that checkpoint, the four typed-boundary checks first failed and
preservation checks passed; units reported 1,649 passed, 11 unchanged skips and
one existing xfail. The relevant model, Authoring and integration batch
reported 628 passed. Eight seeded descriptors compared without differences
(four captures, four expected errors), and four Authoring projections matched.
These are historical local results, not fresh 0.8.5 acceptance.

ArchKeel 0.8.4 could not express the nested opaque map-value decision. The
recorded source-only run had 111 violations; the outer-map-only draft had 103,
with eight allowance FACTs and eight residual nested-object violations. Counted
UNKNOWN was 154. The independent Astra review ruled BLOCKED on that checker.
[ArchKeel #253](https://github.com/rapiddweller/archkeel/issues/253) contains the
complete minimal CLI reproduction and required negative controls.
The full descriptor suite and unseeded parity were not rerun then. Recursive-
definition and pinned Pylint checks remained outstanding; that draft had no
accepted commit, push or CI run.

## Current status: local bounded acceptance

Published ArchKeel 0.8.5 supports the exact depth-1 map-value selectors. The
same-version parent/candidate comparison is 103 -> 95 violations: exactly
eight intended findings removed, with no added or changed remaining finding.
All 204 raw UNKNOWN records retain IDs and semantics; 150 remain counted. The
`constraints.values` generic UNKNOWN has updated source-symbol/evidence
references for its annotation. Baseline new changed 67 -> 63; baseline resolved
stayed 0. Baseline, budget and oracle are unchanged. Fresh QA and Astra review
pass for this bounded local slice. Opaque-value acceptance does not prove type
closure; lazy-supplier UNKNOWN remains visible. See
[Step 96 bounded validation](step-96-dsl-validation.md) for results and limits.

## Task 3: Resume after the published checker fix

Use released ArchKeel 0.8.5. Keep the completed production and test drafts;
do not reimplement Tasks 1–2. Root added the eight exact map-value selectors
(`container_depth: 1`, full `dict[str, object]` annotation) alongside the eight
outer-map selectors. This admits opaque raw values, not proven type closure.

Own only the Makefile checker pin, Amendment 91 and the short target/step
documentation. Pin the checker to 0.8.5 without changing gate logic. Replace
the blocker wording with the supported exact decision and preserve the 0.8.4
failure as history. The bounded local slice is accepted; the whole CE target,
full DSL suite and CI are not claimed. Root owns the amendment receipt, commit
and push.

Independent QA reran the existing behavioral checks with the frozen oracle,
Make units, lint/full MyPy, recursive definitions and pinned Pylint. The same
0.8.5 parent/candidate observations preserve remaining UNKNOWN evidence and
baseline/budget values. Final Astra review approved the bounded code slice;
whole-goal and delivery approval remain open.

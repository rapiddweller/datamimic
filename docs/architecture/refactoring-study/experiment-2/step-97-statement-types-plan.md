# Step 97: scalar statement boundaries

Base `6901abf0`, published ArchKeel 0.8.5. Astra selected these getters after
checking models and runtime consumers. Statements expose parsed configuration;
tasks execute it. This step changes annotations, not that division of work.

| Statement | Getter | Return |
| --- | --- | --- |
| GeneratorStatement | name, generator | str |
| DatabaseStatement | db_id | str |
| MongoDBStatement | mongodb_id | str |
| MemstoreStatement | id | str |
| ElseIfStatement | condition | str |
| ListStatement | converter | str or None |
| ItemStatement | condition | str or None |

## Independent work

1. Luna QA owns one focused test file under `tests_ce/unit_tests/test_dsl/`.
   Check the eight public return annotations and real model/statement values,
   including absent and empty optional strings. Reuse existing consumer tests.
   Record annotation RED separately from passing behavior checks before edits.
   Production, contracts, descriptors, oracle, gates and Git are read-only.
2. Luna implementation owns only the seven statement files listed above.
   Trace models and consumers independently. Wait for root's RED confirmation,
   then add eight return annotations and the existing generator name field's
   explicit str annotation. No runtime edits, wrappers, coercion, aliases,
   casts or contract exceptions.
3. Root freezes affected descriptor/projection outputs before source edits,
   compares parent and candidate with the same checker, reviews the diff and
   asks Astra for independent final acceptance before commit/push to PR274.

## Acceptance

Expected measurement: eight missing-return-annotation UNKNOWNs disappear;
accept only the actual measured IDs and counts, including their corresponding
DSL aggregate update. No added violation, unrelated UNKNOWN semantic change,
baseline/budget growth or lost scan coverage.
Run focused tests, relevant parser/task/integration suites, Make units,
lint/full MyPy, recursive definitions, physical-target checks, pinned Pylint
and frozen affected descriptors/projections. Full-suite and CI claims remain
separate from this checkpoint.

Astra approved `self._name: str = model.name` after full MyPy exposed the
base field's optional type. The model requires str; no later mutation widens
it. Keep the base optional type and initialization behavior unchanged. Prove
AST equality after normalizing only this exact assignment and the eight
named return annotations. Check missing/None generator-name rejection.

The eight-case parent snapshot has five CAPTURED cases and three UNVERIFIED
nested-list cases. Keep the full comparator failure; compare the five proved
cases and four projections separately. Astra permits this annotation-only
checkpoint with those three evidence gaps still open, not affected-DSL parity
acceptance. A separate list-evidence step must precede behavioral work there.

Exclude `EchoStatement.value`: a valid empty XML element reaches `EchoTask`
with None and raises TypeError. That needs an explicit error/empty-text policy,
not a dishonest str annotation. Also exclude `get_parent_full_name`; optional
ancestry handling needs its own investigation. Keep both findings visible.
Generator-registry ownership, broader type boundaries, full DSL equivalence,
coverage, EE alignment and complete report navigation remain open.

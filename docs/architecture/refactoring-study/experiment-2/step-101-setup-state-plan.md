# Step 101: setup state and copy boundary

Base `37c7510d`; published ArchKeel0.8.5. Spec: [protocol](protocol.md).
Astra decided the coherent namespace/global-state and copy transaction batch.
Root owns documentation, Git and acceptance. Independent Luna QA and code
agents own disjoint files; neither commits or spawns agents.

## Global constraints

Preserve all runtime behavior and existing XML. No baseline, allowance,
budget, gate, oracle, schema, public class identity or owner changes.
No wrappers, casts, Any, generator-only fiction, new dependencies or EE/
ArchKeel edits. Preserve supplied dictionary identity and shared copy memo.
Keep properties and mixed generator cache debt explicit and unchanged.

## Task 1: independent QA

Own only `tests_ce/unit_tests/test_contexts/test_setup_context.py` and ignored
evidence. Inspect actual Context construction, callers and include/copy flow.
Extend existing tests, reusing `_context`, not a parallel fixture framework.

Add a compact annotation-contract check for the signatures in Task2; observe
RED against the original source before the implementation gate opens. Add
real behavioral checks for supplied/replacement namespace map identity,
arbitrary objects/classes, shared memstore identity, copy aliasing, namespace
TypeError fallback in single-process mode, multiprocessing exception/cause,
and propagation of a non-TypeError. Existing client alias/global sharing/
seed/default tests remain; avoid duplicate coverage. Behavioral checks may
already pass; only annotation-contract RED is expected.

Then run focused context tests, `make test-unit`, `make lint`, full
`make typecheck`, and the relevant expression/script/include/memstore/state
machine integrations using normal pytest plugins. Report exact warnings,
skips and outcomes. Escalate localhost-socket denial; do not disable plugins.

## Task 2: independent implementation

Own only `datamimic_ce/engine/runtime/contexts/context.py` and ignored evidence.
Independently trace producers and consumers; wait for root's RED gate.
Apply annotations only:

- `__init__`: namespace/global_variables `dict[str, object] | None`, result None.
- `_global_variables`: `dict[str, object]`.
- namespace getter: `dict[str, object]`; setter value same, result None.
- global_variables getter: `dict[str, object]`.
- memstore_manager getter: `MemstoreManager`.
- update_with_stmt result: None.
- `__deepcopy__`: memo `dict[int, object]`, result SetupContext.
- `_deepcopy_namespace`: same memo, result/accumulator `dict[str, object]`.

No executable-expression changes. Arbitrary Python values belong to the
dynamic DSL namespace; scalar/JSON narrowing would change its contract.
Properties and generators retain their current unresolved annotations.
Run focused tests, package lint/typecheck and self-review the source-only diff.

## Task 3: independent cyclic-boundary QA

The typed memstore getter exposed `GenerateStatement.cyclic: bool | None`
reaching IO's existing bool contract. Astra decided that omitted cyclic means
False at the Runtime caller, matching the other memstore routes.
Own only `tests_ce/unit_tests/test_util/test_source_routing_order.py` and
ignored evidence. Add one parameterized test using its existing
`_generate_source_statement`/`_generate_source_context` helpers and a
`Mock(wraps=real_memstore)`, not a replacement selection implementation.

Seed two rows with nested objects; page skip1/limit4. Cases:
None -> False and [2]; False -> False and [2]; True -> True and [2,1,2,1].
Assert the actual boundary bool, build flag, retained finite-row identity,
cyclic nested-object isolation and unchanged stored rows. Run before source
fix; only omitted-value argument assertion should fail. Then wait for root's
gate, rerun green, full units/lint/MyPy and relevant memstore integrations.
Normal pytest plugins; no fixture, descriptor or source edits.

## Task 4: cyclic default normalization

Own only `datamimic_ce/engine/runtime/tasks/sources/generate.py` and ignored
evidence. Independently trace the flagged Runtime-to-IO call and sibling
routes. Wait for Task3/root RED. Change only that get_data_by_type argument
from `stmt.cyclic` to `bool(stmt.cyclic)`; do not widen IO/DSL signatures.
This resolves the existing optional DSL default, not an invalid-type cast.
All None/False/True row/window/copy semantics must remain unchanged.
Run focused tests, package lint/MyPy and source self-review.

## Acceptance

Root independently verifies runtime/copy semantics and compares fresh decoded
0.8.5 observations. Predicted source-only counts:93/141 ->102/134 violations/
counted UNKNOWN. Seven missing annotations become decided; map/object debt
is exposed, not exempted. Accept only the measured semantic delta, not that
prediction. Physical/import/cycle structure must remain unchanged.
The Context executable AST stays identical after stripping annotations.
The only executable addition is the explicit optional-cyclic default above;
its resolved bool call is an expected observation delta. Full MyPy must pass.

Use unchanged replay/projection machinery and reject incomplete captures.
Astra independently reviews spec and quality before a checkpoint to PR274.
Full930/service/EE parity,90% coverage and all-depth report acceptance remain
open. The Domain initializer ownership gap is a separate next contract step.

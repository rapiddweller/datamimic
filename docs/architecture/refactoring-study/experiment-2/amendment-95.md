# Amendment 95: native Python scripting state

2026-10-02. Astra, delegated architect; base `7d6fb7fd`.

The shipped database-mapping script imports public Context/SetupContext.
Scripts define classes, functions, instances and user-named records; these
namespaces cannot be a fixed business record. Python deepcopy's identity-keyed
memo is likewise not a business model. Keep the public types and native maps;
an opaque wrapper would add no invariant. This corrects the target, not source.

RUNTIME-API-TYPES admits only the positions below, qualified under
`datamimic_ce.engine.runtime.api.`, each with explicit `field_path: ""`.
Each map has two entries with the same full annotation: no depth and
`container_depth: 1`. Scalar rows have one entry without depth. Total: 22
exact permissions at 12 positions. No wildcard or blanket object/map waiver.

| Qualified suffix | Position | Annotation |
|---|---|---|
| Context.evaluate_python_expression | local_namespace | dict[str, object] \| None |
| Context.scope_content | return | dict[str, object] |
| Context.get_content_variables_products | return | dict[str, object] |
| SetupContext.__init__ | namespace | dict[str, object] \| None |
| SetupContext.__init__ | global_variables | dict[str, object] \| None |
| SetupContext.namespace | return | dict[str, object] |
| SetupContext.namespace | value | dict[str, object] |
| SetupContext.global_variables | return | dict[str, object] |
| SetupContext.eval_namespace | return | dict[str, object] |
| SetupContext.__deepcopy__ | memo | dict[int, object] |
| Context.evaluate_python_expression | return | object |
| SetupContext.get_dynamic_class | return | object \| None |

Source types already match. Namespace identity, shared globals, scope
precedence, memo aliases and copy-failure behavior must remain unchanged.
Consumers still validate converters; expression results still reject direct
functions/modules. This is not a scripting sandbox or a claim that all
consumers accept every object.

Properties, mixed generator-cache behavior, source-length and demographic
maps remain separate debt. External/inherited UNKNOWN remains UNKNOWN.
Source, XML, public ownership, baseline, budgets, oracle and gates stay fixed.
Keep old/corrected observations and require exact removed findings, permission
evidence, unchanged UNKNOWNs and failing negative selector/type probes before
checkpoint. Whole-experiment acceptance remains open.

Evidence: [implementation plan](step-103-scripting-state-plan.md); independent
source trace and decision at `/private/tmp/ce-next-boundary-decision.md`.

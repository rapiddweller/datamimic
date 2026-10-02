# Amendment 01 — split the dynamic-execution exception

Date: 2026-09-22. Decided by: architect/orchestrator. Before implementation commit 1.

The frozen `NO-MAGIC-CONTROL-FLOW` rule grouped dynamic execution with `Any`, reflection, casts,
and string dispatch, then exempted the runtime evaluation and plugin modules from the whole group.
ArchKeel applies an allowed source to every construct in a rule, so that wording would also allow
`Any`, `getattr`, and string dispatch in those modules.

The rule is split. Untyped and reflective escape hatches have no exemption. Only `eval`, `exec`,
and dynamic import retain the two explicit runtime owners. This narrows the target; it grants no new
permission.

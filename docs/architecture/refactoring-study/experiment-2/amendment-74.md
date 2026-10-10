# Amendment 74: declare statement branch and memstore manager ownership

Date: 2026-09-29. Decision: Astra.

`ConditionBranchStatement` and `MemstoreManager` are already owned by the nested
DSL statements and Runtime storage contracts. Declare each at its existing root
component boundary so cross-component type references resolve. Keep both out of
`declarations.public_api`; this adds no facade export and changes no source or
runtime behavior.

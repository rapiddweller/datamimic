# Amendment 94: Pre-run factory Generate lookup

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

`find_generate_statement_by_name(statement, entity_name)` is owned by DSL
statement traversal and exported through `engine.dsl.api`. It preserves the
existing factory search: match the first depth-first `GenerateStatement`, and
do not descend through non-Generate composites before execution. Runtime
lifecycle delegates its factory lookup to this DSL operation.

The executed-condition lookup remains separate. Factory error messages,
validation mutations, and Ray environment initialization are unchanged.

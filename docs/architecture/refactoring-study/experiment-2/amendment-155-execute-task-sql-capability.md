# Amendment 155 — injected SQL client capability

Date: 2026-10-08. Decision: architect-approved compatibility clarification.

`ExecuteTask` keeps accepting injected clients that provide
`execute_sql_script(query)`. The `SqlScriptClient` Protocol is the narrow static
contract; do not require a concrete `RdbmsClient` or probe the method before
invocation. Runtime selects the configured target and IO performs one direct
call, preserving dynamic implementations and native errors. This changes no
descriptor semantics.

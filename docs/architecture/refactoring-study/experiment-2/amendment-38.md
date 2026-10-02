# Amendment 38: remove Authoring rules' IO dependency

The linter adapter now supplies buffered exporter names through `LintContext`;
cross-statement rules stay IO-free. The shared target-call parser moves to DSL
input parsing, used directly by the exporter registry and dry-run adapter. No
compatibility shim is added; valid descriptor behavior is unchanged.

The parser preserves the existing AST behavior, including positional-argument
ignoring and `**kwargs` handling. For non-string literal target names, DM401 now
returns a diagnostic instead of crashing; runtime parsing itself is unchanged.

Evidence: candidate ArchKeel violations fall from 23 to 20, with 71 UNKNOWN
unchanged and no new violation. Recursive target checks, Ruff, MyPy, the cycle
gate and the non-service suite pass (1969 tests, 13 skips). All 930 descriptor
statuses and seeded outputs match S3G18. Two unseeded captures differ: a
dynamic Memstore count, and a Boolean-conditional demo field that reappears on
the same code when repeated. The frozen capabilities hash still differs from
step 0.

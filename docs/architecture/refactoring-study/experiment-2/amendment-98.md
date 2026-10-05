# Amendment 98: disclose native Runtime property types

2026-10-05. Astra approves the bounded source-annotation plan, not an architecture
gate PASS. SetupContext properties are a mutable, user-keyed `dict[str, object]`:
native Python callers can supply integers and nested objects. Includes
update the supplied dictionary in place. None creates a fresh dictionary.

Annotate only constructor, backing field, getter and setter. Preserve defaults,
identity and deepcopy semantics. No request/parser widening or generator change.
Missing annotations becoming explicit map/object findings is honest disclosure,
not a reason to change the baseline or add permissions.

Contracts, allowances, budgets, gates, descriptor files and oracle stay frozen.
Final zero-violation and zero-material-UNKNOWN requirements are unchanged. The
affected Authoring allowance, Errors ownership and report acceptance still need
their separately tracked checker fixes. See [Step 106 plan](step-106-properties-plan.md).

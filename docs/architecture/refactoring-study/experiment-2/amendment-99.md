# Amendment 99: truthful capture rows

Agent-derived decision by Astra under Alex's delegated architecture authority;
CE base `26e01b15b5127044a32db64d0206a9d30a057a4e`. This approves the bounded
CE 5.0 source specification, not a green architecture gate or full DSL acceptance.

Capture stores arbitrary native rows, not only dictionaries. A valid seeded XML
descriptor with `<key name="#text" constant="scalar"/>` and one explicit
`TestResultExporter` target returns `['scalar', {'#text': 'scalar'}]` in test
mode: page capture and lazy capture share storage. Preserve both entries, order,
counts, live dictionary/list/row identity and nested native values.

IO storage/getter and Runtime/Python result surfaces use
`dict[str, list[object]]`, retaining their existing optionality. No wrapper,
copy, coercion, filtering, capture-stream deduplication or request widening.
TestResultExporter.consume retains its existing variadic tuple compatibility.

Only factory overlays (`custom_data is not None`, including `{}`) require
`isinstance(row, dict)` immediately before each existing row.update call.
Otherwise raise `TypeError("Factory custom_data requires dictionary rows")`.
Preserve existing capture/entity/count checks first, dict-subclass overrides,
update exceptions and sequential batch mutation. No-overlay results stay broad.

Compatibility change: non-dictionary update-capable objects formerly supported
by overlays become unsupported; scalar overlay AttributeError becomes TypeError.
EE has not adopted this policy. No EE parity or external-caller compatibility
claim. Existing successful dictionary overlays and raw DSL captures stay unchanged.

Freeze machine contracts, allowances, baseline, budgets, gates and oracle.
Newly exposed type findings remain red; this amendment grants no type permission.
Independent source review permits a bounded red checkpoint: 86 -> 87 findings,
including the newly exposed `runtime.api.run` / `return.captured` map. Strict
oracle FAIL and UNKNOWN remain; this does not satisfy final acceptance.
Evidence and independent source review: `step107-next-boundary-decision.md`,
`step107-factory-decision.md`, `probe_scalar_capture.py` in scratch
`ce-archkeel-090-20261005.GF5VUk`; durable execution proof belongs in the step report.

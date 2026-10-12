# Amendment 186 — Runtime properties policy

2026-10-10. Decision: Astra, delegated architect. Base `34f889e087c8274a277ae56a9c70efa9c85ab97d`.

Runtime holds the mutable, user-keyed native properties dictionary. `SetupTask`
passes the supplied dictionary to `SetupContext`; `None` creates a fresh one,
while empty and populated dictionaries keep their identity. The setter replaces
it, `IncludeTask` updates it in place with string file properties, and deepcopy
copies its native values with the shared memo and existing error behavior.

`RUNTIME-API-TYPES` gains exactly two `SetupContext.__init__` `properties`
selectors for the complete `dict[str, object] | None` annotation and empty
field path: one for the outer dictionary and one for its native value at
`container_depth: 1`. The latter is accepted opacity, not type closure. The 35
previous selectors and all other rules stay unchanged. No DTO, source, baseline,
budget, oracle, SQL155 or dependency change is part of this amendment.

This policy does **not** complete the Properties source contract. The full
`dict[str, str] | dict[str, object]` correction across adapter, request, parser
and Runtime remains required by Astra's Slice 168 source decision.
The current bare `SetupTask` forwarding and narrower request/parser types do
not establish end-to-end static compatibility; external typed callers remain
UNKNOWN. No read-only Mapping, arbitrary `dict[str, int]`, or serialization
compatibility is claimed.

The published ArchKeel 1.1.1 report on this candidate records 22 → 20 findings,
removing only `VIO-99cade1ffdf51955` and `VIO-ec073b392382b228`. All 20
remaining records and all 254 canonical UNKNOWNs are unchanged. Two allowance
facts are added, one with `accepted_opacity=true`; 11 existing Runtime allowance
facts gain this amendment's provenance only. Source digest, symbols, imports,
calls, modules and coverage are identical to the 1.1.1 pre-update packet.
Four wrong selector fields restore both property findings; removing either
entry or changing the native depth restores one. In a separate published-CLI
source fixture, object keys and wrong container/native depth restore both
property findings, while the neighboring control and UNKNOWNs remain visible.

LOCAL VERIFIED: the exact selector guard failed before the two entries and
passed after. Three behavior tests confirm noncopyable native property errors,
direct/dotted falsy substitution and scalar-intermediate `AttributeError`.
The final focused cohort passes 115 tests, definition checks pass 13, and the
CE unit suite passes 2341 (11 skipped, one expected failure, two Pydantic
serializer warnings). Ruff and full-package MyPy (488 files) pass. The
standard Makefile ArchKeel and definition launchers cannot write the shared uv
cache in this isolated sandbox; definition tests ran with the project venv and the report
ran from the installed published 1.1.1 environment. Native
`validate --baseline` exits 2 with the same 19 existing diagnostics, 14
baseline-new groups and zero resolved groups as before; it emits no machine
amendment. Independent QA remains pending. CI-ONLY VERIFICATION: this
candidate has not run in CI.

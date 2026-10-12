# Amendment 213 — native open payloads

2026-10-11. Decision: approved by independent Astra review.

Schema 3.3 records three existing compatibility boundaries exactly:

- IO's `read_generate_file_source` returns `rows: list[dict]`. File column
  names and values belong to the input data, without a fixed row DTO.
- Runtime's `SetupContext.__init__` accepts `generators: dict | None`.
  The mutable registry retains its existing keys, values and identity.
- IO's `read_nested_key_source` permits the native `object` leaf only in
  the literal `list[dict[str, object]]` arm, at container depth 2.

Amendment 176's existing client-registry permission now selects only the literal
`dict[str, RegisteredClient]` arm of the unchanged nullable annotation.
The `RegisteredClient` payload alias retains its independent UNKNOWN.

These permissions accept opacity at those exact positions. They prove no key,
value, recursive `JsonValue` or arbitrary named-alias contract. IO still owns
reading and selection; Runtime owns the generator registry. Source behavior,
baseline and budgets stay unchanged. A fresh report and independent UNKNOWN
assessment remain required for completion.

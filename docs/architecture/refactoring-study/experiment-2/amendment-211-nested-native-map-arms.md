# Amendment 211 — nested native map arms

2026-10-11. Decision: agent, delegated by Astra.
Base `bae4f6059b5e474ff454b97837e47dcc739062cc`.

Use schema 3.2's explicit literal-arm selectors at the exact
`read_nested_key_source` return signature. Preserve Amendment 210's native
JSON object-root permission and admit the immediate CSV string-row and Memstore
native-row maps. IO owns reading and selection; input keys remain data.

Amendments 181/183/188 and the retained native reader controls support this
intent. This supersedes Amendment 210's contained-map hold only for those two
maps. Object leaves, recursive `JsonValue` and every UNKNOWN remain assessed
separately. Source, native values, identity, errors, owners, baseline and budgets
stay unchanged. Migration and actual finding closure await independent review
and a fresh same-producer comparison.

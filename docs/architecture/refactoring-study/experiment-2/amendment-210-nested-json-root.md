# Amendment 210 — nested JSON object root

2026-10-11. Decision: agent, delegated by Astra.
Base `868aaab4140a161e142a3653e7b81d1187272a54`.

`read_nested_key_source` preserves the native mutable string-keyed JSON object
root. Its keys are input data, not fixed DTO fields. Admit only the unique
outer map at the exact full return signature in `IO-API-TYPES`, under schema2.1.

Contained CSV/JSON/Memstore maps, object leaves and recursive `JsonValue` remain
independently assessed. Native values, identity, errors and reader ownership stay
unchanged. No source, schema, baseline or budget change.

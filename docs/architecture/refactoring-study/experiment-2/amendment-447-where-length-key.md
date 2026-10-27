# Amendment 447 — where= in the source-length key

2026-10-27. Decision: open. An independent Astra review must approve it and rebind `contract_digest`.

Runtime caches the row count of a statement source in `SetupContext.data_source_len`. Amendment 176 fixed
its key as `tuple[str | None, str | None]`: the statement name and the source. Issue #447 adds `where=`.
Two statements with the same name and the same file but another `where=` shared one count, so
`datamimic run` truncated the second statement silently. Build refuses duplicate product names, so only a
run can reach this case.

The key becomes `(full_name, source, where)`. The third element is the `where=` text of a
`<generate>`/`<iterate>` and `None` for a variable, a nested key and a statement without `where=`.

`RUNTIME-API-TYPES` changes exactly two existing selectors of Amendment 176, with an empty field path:

- `SetupContext.__init__` `data_source_len`: `dict[tuple[str | None, str | None, str | None], int] | None`
- `SetupContext.data_source_len` return: `dict[tuple[str | None, str | None, str | None], int]`

No other selector, source, ownership, dependency, baseline or budget changes. `CountSourceRequest.source_id`
keeps its two-element type; IO does not read it. A string encoding of `where=` in one of the two existing
elements was rejected: it is a string-shaped identity, and a statement name can equal a `where=` text.

LOCAL VERIFIED: `test_runtime_boundary` pins the two selectors. The run test
`test_statements_on_one_file_with_other_conditions_keep_their_own_rows` fails with the old key
(`[3, 5, 1, 2]`) and passes with the new key (`[3, 5, 1, 2, 4]`).
NOT VERIFIED: the completion gate. It stops with "Independent review does not match the current Target and
analyzer." until the review records the new `contract_digest`.

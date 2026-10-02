# Step 66: narrow sequence source and count values

`SequenceTableGenerator` rejects a missing database name before storing
`_source_name` as `str`, then uses that name directly for both client lookups.
It also reads generate count once, checks for `None`, and converts the narrowed
value. Successful sequence behavior stays unchanged; a missing count now has a
specific error. Fake-client tests cover both missing inputs.

LOCAL VERIFIED: 10 focused sequence-table tests passed, including default and
explicit names, `pre_execute`, missing count, and missing database name. Full
package MyPy (491 files), targeted Ruff, and `git diff --check` passed. No live
database or CI run was performed.

# Amendment 72: match the exact smoke-export findings

Date: 2026-09-29. Decision: Astra.

Amendment 62 intended exact exceptions for dynamic smoke-export values, but
candidate ArchKeel `9443541` identifies two distinct findings at each field:
the open `dict[str, object]` container and its nested `object` value. Keep the
existing container allowances and add an `object` allowance for each exact
`request.params` and `request.rows` path. Keep the production types unchanged:
`params: dict[str, object]` and `rows: list[dict[str, object]]`.

A contract test pins both container shapes. These exceptions do not establish
runtime validation or permit unrelated open control fields. Amendment 62's old
count is historical evidence, not proof that its allowance still matches the
current analyzer.

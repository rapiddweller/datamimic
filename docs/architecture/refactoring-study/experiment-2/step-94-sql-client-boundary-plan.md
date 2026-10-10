# Step 94: SQL ownership and client types

Base: `b15d265`. Astra approved this bounded CE 5.0 change on 2026-10-02.
SQL capability belongs to IO. Runtime owns client references, not SQL dispatch.
No checker, baseline, descriptor or oracle edits. Amendment 90 later records
the explicit native-registry target correction, with three exact positions.

Known break: SQL accepts `RdbmsClient` and subclasses, not arbitrary injected
clients. Unsupported clients now raise `TypeError`, not incidental
`AttributeError`. External injection usage is UNKNOWN. Valid database DSL,
query text, transactions, documented entry points and resource lifecycle stay
unchanged. This is not a claim that historical ArchKeel #228 is fixed.

## Task 1: Independent tests

Own only tests in the isolated checkout. First-pass inventory is already
independent. Write failing acceptance tests before Task 2 starts.

Files: `tests_ce/unit_tests/test_clients/test_client_operations.py`,
`tests_ce/unit_tests/test_contexts/test_setup_context.py`, and new
`tests_ce/unit_tests/test_task/test_execute_io_boundary.py`.

- IO operation `execute_sql_script(client: Client, query: str) -> None` is
  exported through `io.api`. Accept real uninitialized `RdbmsClient` and true
  subclass overrides. Preserve query text, one call, underlying exception.
- Reject Mongo, plain Client and a Client-only SQL subclass with
  `TypeError("Client does not support SQL script execution")`, without calling
  the injected method. Do not rely solely on MagicMock class spoofing.
- Runtime resolves content before lookup. Missing and None targets retain
  `KeyError(id)` and `KeyError(None)` after interpolation. Keep SQLite inline,
  script and URI readback, literal braces and parse negatives unchanged.
- Registry keeps supplied/set dictionaries and clients by identity. Cover
  overwrite, missing lookup, namespace binding, disposal-before-copy, shared
  deepcopy memo, TypeError-only fallback and other exception propagation.
- Check typed registry annotations and a negative static type probe; do not
  add runtime registration validation.

Use existing helpers. No changes to old expected DSL output. Report exact RED
command/failures separately from already-passing compatibility cases. Do not
edit production, contracts or Git. Root runs normal-plugin acceptance too.

## Task 2: Independent implementation

Own only these five production files under `datamimic_ce/`:

1. `engine/runtime/contexts/context.py`: constructor optional
   `dict[str, Client]`, storage/getter/setter `dict[str, Client]`;
   `_deepcopy_clients(memo: dict[int, object]) -> dict[str, Client]`, typed
   result and `_clients: dict[str, Client]`; `add_client -> None`;
   `get_client_by_id -> Client | None`.
   Preserve identity, mutation, namespace binding and disposal/copy behavior.
2. `engine/io/clients/operations.py`: add
   `execute_sql_script(client: Client, query: str) -> None`;
   `isinstance(client, RdbmsClient)`, otherwise
   `TypeError("Client does not support SQL script execution")`, then delegate.
3. `engine/io/api.py`: export the operation, not concrete client classes.
4. `engine/runtime/tasks/flow/commands/execute_task.py`: after unchanged
   content resolution/interpolation, guard None target with `KeyError(None)`;
   retain missing-id dictionary lookup and delegate through IO.
5. `engine/runtime/tasks/sources/variable.py`: use
   `client is None or not is_database_client(client)` in the existing guard;
   retain its diagnostic without a duplicate branch.

No TypeGuard, new Protocol, base Client SQL method, casts, getattr, lifecycle
changes, generator/config cleanup or ArchKeel edits. Extra files require a
concrete full-package MyPy failure and root review. Run focused tests, existing
Make lint/typecheck and inspect the diff. Do not edit tests or Git.

## Root acceptance

Review source and tests independently; ask a fresh Astra reviewer. Run normal
unit suite, relevant SQL integrations, full MyPy/lint, definition/cycle gates,
CLI/import smoke, eight before/after descriptors and four projections.
Regenerate published ArchKeel 0.8.4 HTML/JSON, compare against b15; preserve
FAIL/UNKNOWN honestly. Update only the changed module responsibility if needed.
Record accepted breaks and exact evidence. Stage only the verified batch;
preserve all primary dirty drafts. Push the existing Draft PR, no merge.

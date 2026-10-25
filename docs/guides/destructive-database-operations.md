# Destructive database operations

This guide is the single source for selective delete, clear and drop in DATAMIMIC CE 5.0
(BC-4.0-016). The target name states the effect. Use the client id as the prefix:
a client with `id="db"` gives `db.delete`, `db.clear` and `db.drop`.

## Contract

| Suffix | RDBMS | MongoDB |
|---|---|---|
| `.delete` | Delete the rows whose primary keys the row source returns. | Delete the documents the row source returns, by `_id`. |
| `.clear` | Remove every row. Keep the table, indexes and constraints. | `delete_many({})`. Keep the collection and its indexes. |
| `.drop` | Not supported. Use `<execute>` with DDL. | Drop the collection. |

`update` and `upsert` are unchanged. Each client family accepts only its own suffixes.
Another suffix fails with `I320`, and the message lists the allowed ones.

## Descriptor forms

```xml
<!-- Delete the selected rows -->
<generate name="delete_old" source="db" selector="SELECT id FROM orders WHERE status = 'old'"
          targetEntity="orders" target="db.delete"/>

<!-- Remove every row; keep the table -->
<generate name="clear_orders" targetEntity="orders" target="db.clear"/>

<!-- Drop a MongoDB collection -->
<generate name="drop_orders" targetEntity="orders" target="mongo.drop"/>
```

## Rules for `clear` and `drop`

A `clear` or `drop` is a one-time statement. It runs once, before any count, source or worker exists.
It has these properties:

- It is at the root of `<setup>`. A nested `<generate>` or an `<include>` inside a `<generate>` is refused.
- It names `targetEntity`.
- It has no `source`, `sourceEntity`, `selector`, `count`, `script`, interval attributes or child statements.
- It has exactly one target.
- Its client exists and is not read-only.

A breach fails with `I928` before any database access. A read-only client fails with `I907`.
An `<include>` at the root of `<setup>` can hold a `clear`. The statements run in document order.

## Rule for `delete`

A `delete` that reads a database `source` needs a `selector`. Without one, the delete removes
every row the source returns, and that is a `clear` written as a delete. It fails with `I928`.
An empty or blank `selector` counts as no selector.

These forms stay valid:

- A `delete` on generated rows (no `source`) deletes by the keys of the generated rows.
- A `delete` with a file `source` deletes the rows the file lists.
- A MongoDB selector with an empty filter (`filter: {}`) stays valid in CE 5.0.
  Prefer `mongo.clear` for that intent, because it states the effect.

Migration examples are in [the migration guide](../migrations/authoring-errors.md).

## Execution

- PostgreSQL and MSSQL use `TRUNCATE TABLE`. If the database refuses it
  (for example, a foreign key references the table), CE runs a full-table `DELETE`.
  Other databases use `DELETE FROM`.
- A successful `TRUNCATE` reports the row count as `unavailable`. It never reports 0.
- Put the `clear` of a child table before the `clear` of its parent table when foreign keys exist.
- A `clear` before a file export does not change the exported file.

## Log lines

```text
OPERATION | rdbms.clear | table=<t> | action=clear | backend_action=truncate|delete_all | deleted_count=<n|unavailable>
OPERATION | mongodb.clear | collection=<c> | action=clear | deleted_count=<n>
OPERATION | mongodb.drop | collection=<c> | action=drop
```

## Authoring

- `datamimic authoring lint` knows the operations of each client family (rule `DM401`).
  A `clear` or `drop` needs no `count` (rule `DM202`).
- A bounded run (`dry-run`, `run` without `--allow-side-effects`, Build) checks the shape,
  then skips the statement. It reports a `not_executed` warning. It never clears an external database.
- `authoring run --allow-side-effects` runs the statement on a private copy of the workspace.
- Build proves only the products. A project with a `clear` and no product is rejected.
  A skipped `clear` does not prove its effect. Check the database state with `datamimic run`.
- A `delete` of a whole database source fails with `I928` in bounded runs and in Build,
  also inside an included step.

## Differences from EE

| Topic | CE 5.0 | EE |
|---|---|---|
| `.delete` without selector | `I928` when it reads a database source | EE 4.x rewrites it to `.clear` or `.drop` and warns with `W003` |
| 4.x compatibility bridge | Not ported | Removed in EE 5.0 |
| Mongo `.delete` with `filter: {}` | Valid | Rewritten to `.clear` with `W003` |
| `iterationSelector` on `<generate>` | Not a CE attribute (CE has it on `<variable>` only) | Accepted as a selector |

## Conformance cases

These cases give the input for the CE/EE parity matrix (#387). Each case has a DSL model or a test.

| Case | Expected result | Evidence |
|---|---|---|
| `db.clear` on one table | The table is empty. Other tables are untouched. | `tests_ce/integration_tests/test_clear_drop_operations/clear_one_table.xml` |
| Clear, then insert | The same rows after every run. | `.../clear_then_insert.xml` |
| Several clears in order | Child, then parent. | `.../clear_in_dependency_order.xml` |
| Clear in an include | The clear runs. | `.../clear_through_include.xml` |
| Clear on a read-only client | `I907`. The rows stay. | `.../clear_read_only.xml` |
| Clear with `source`, `selector`, `count`, `script`, children, a second target or a nested position | `I928` before any database access. | `.../invalid/` |
| `db.drop` on an RDBMS | `I928`. | `.../invalid/drop_on_rdbms.xml` |
| `.clear` with call syntax (`db.clear()`) | `I928`. | `.../refused_call_syntax.xml` |
| Clear or drop inside an include inside a `<generate>` | `I928`. | `.../refused_include_in_generate.xml` |
| PostgreSQL clear | `TRUNCATE`, count `unavailable`, foreign keys intact. | `tests_ce/external_service_tests/test_destructive_operations/` |
| PostgreSQL clear of a referenced table | Falls back to `DELETE`. | same directory |
| Mongo clear and drop | Documents removed, collection and indexes kept (clear) or gone (drop). | same directory |
| Delete of a whole database source | `I928`. Rows stay. | `tests_ce/integration_tests/test_delete_needs_selection/` |
| Delete with a blank selector | `I928`. Rows stay. | same directory |
| Delete with a selector | Only the selected rows go. | same directory |
| Delete by generated keys | The rows with those keys go. | same directory |
| Dry-run and Build of a `clear` | Skipped with a `not_executed` warning. | `tests_ce/unit_tests/test_authoring/test_clear_drop_authoring.py` |

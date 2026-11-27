# Build projects

Each example is a project: write the XML as `datamimic.xml` and the JSON as
`acceptance/build.json` in one directory, then run `datamimic authoring build <dir>`.
`outcome: "ready"` lists every file the proof read with its digest; changing any of
them voids the proof. Expectations and roles live in `acceptance/build.json`, so they
survive edits to the XML. Use `datamimic authoring schema --name build_request_v5`
for every acceptance field.

## Nested foreign keys

Two parents, two child rows per parent. The child carries the real `parent.id`;
a randomly selected valid parent key does not establish per-parent cardinality.

```xml
<setup rngSeed="7">
    <generate name="parents" count="2">
        <key name="id" generator="IncrementGenerator"/>
        <generate name="children" count="2">
            <key name="parent_id" script="parent.id"/>
        </generate>
    </generate>
</setup>
```

```json
{
  "version": "5.0",
  "product_roles": [
    {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
    {"product": "children", "field": "parent_id", "role": {
      "kind": "foreign_key", "parent_product": "parents", "parent_field": "id"
    }}
  ],
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "parents"}, "count": 2},
    {"kind": "per_parent_count", "subject": {
      "kind": "per_parent", "parent_product": "parents", "child_product": "children"
    }, "count": 2}
  ]
}
```

## Memstore readback

A `<generate source>` readback is a product of its own: the producer identifier and
the consumer FK role pair make its integrity part of the proof. Merely declaring a
memstore target does not establish a reader.

Write a file for a product with the producer's own target: `target="mem,CSV"`.
Add a `<generate source="mem">` readback only when a later step reads the rows as a
product. A later step that only uses the rows reads them with
`<variable name="rows" source="mem" sourceEntity="parents" storage="data" distribution="ordered"/>`
inside its `<generate>`; without `storage="data"` each record gets one row. That
read needs no role pair; Build checks that the store still holds the captured rows.
Do not add an `export_*` block that only repeats a product.

Declare the store as `<memstore id="mem"/>`. EE has one built-in `mem` store and
ignores the declaration with warning `W005`, so this form runs in CE and EE.
Other ids are a CE-only extension.

Read an entity with `sourceEntity`. A product writes the entity named by
`targetEntity`, else its own name. On a memstore source, `type` names only the
entity that the step reads.

```xml
<setup rngSeed="7">
    <memstore id="mem"/>
    <generate name="parents" count="2" target="mem">
        <key name="id" generator="IncrementGenerator"/>
    </generate>
    <generate name="readback" source="mem" sourceEntity="parents" distribution="ordered">
        <key name="id" script="this.id"/>
    </generate>
</setup>
```

```json
{
  "version": "5.0",
  "product_roles": [
    {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
    {"product": "readback", "field": "id", "role": {
      "kind": "foreign_key", "parent_product": "parents", "parent_field": "id"
    }}
  ],
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "readback"}, "count": 2}
  ]
}
```

When a Memstore product has a composite identity, declare the first field as
`field` and the remaining fields in `role.additional_fields`. On the readback,
declare one `foreign_key` role per identity field, mapped by `parent_field`.
Build checks the full combination for uniqueness and verifies every identity
appears exactly once on both sides, regardless of row or role declaration order.
Components can repeat and can be null, but each field must be present. This is
only for Memstore readbacks; nested foreign-key roles are unchanged.
See the [two-field example](../../tests_ce/scenarios/s61_memstore_composite_identity).

## Time series

Two parallel series over three hourly points produce six rows. The end is
exclusive; `count` on `generate` is the parallel series count.

```xml
<setup rngSeed="7">
    <generate name="readings" count="2" start="2026-01-01T00:00:00" end="2026-01-01T03:00:00" interval="PT1H">
        <key name="reading" constant="ok"/>
    </generate>
</setup>
```

```json
{
  "version": "5.0",
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "readings"}, "count": 6}
  ]
}
```

## File sources

`<iterate source="data/fixtures/orders.ent.csv">` copies every column of the file
into each row, also the columns that no `<key>` names. Two attributes select from
a file source:

- `where="<python bool>"` keeps the rows for which it is true. Count, `cyclic`,
  distribution, paging and worker chunks then work on the kept rows. Without
  `count` the count is the number of kept rows.
- `columns="a, b"` lists the source columns that go into the output, in that order.
  The other columns stay readable by keys and scripts as row variables (bare name
  or `this.<column>`). A key with the name of an unlisted column writes it.
  `columns=""` copies no column.

```xml
<setup rngSeed="40961">
    <iterate name="order_report" source="data/fixtures/orders.ent.csv" distribution="ordered"
             where="int(amount_cents) &gt;= 1000" columns="order_id, customer_id"
             target="JSON" exportUri="order_report">
        <key name="net_cents" script="int(amount_cents)"/>
    </iterate>
</setup>
```

```json
{
  "version": "5.0",
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "order_report"}, "count": 3},
    {"kind": "range", "subject": {"kind": "product", "product": "order_report"}, "field": "net_cents", "minimum": 1000, "maximum": 1000000},
    {"kind": "field_absent", "subject": {"kind": "product", "product": "order_report"}, "field": "amount_cents"}
  ]
}
```

CSV columns arrive as strings: cast them in `where` and in scripts. A Build
`range` expectation requires numeric captured values; cast source text in the
model rather than applying a range to the original text column. `where` reads
one row: its columns, `this`, and the expression functions. It must not read the
clock or draw random values, and it cannot read `parent.`, variables or setup names.
A column name with a space or a Python keyword is `this['order id']` or
`this['class']`. Omit `count` when you use `where`: a `count` above the kept rows
without `cyclic` stops at the kept rows, and Build cannot prove that capture
complete (capture `unknown`). The same model without `where` is ready, because
Build counts a plain file before the run. `where` and `columns`
apply to file sources only (CSV, `.ent.csv`, `.wgt.csv` with a header, JSON, XML,
XLSX, fixed-width, DbUnit), not to a memstore, a database (use `selector=`) or
`sourceScripted`. `where` does not combine with `offset`. Build counts the kept rows
in its bounded run; more than `max_count` kept rows (default 10) stop the run with
`I800`. `unique="True"` compares whole source rows, not only the listed columns.

A filter that depends on the parent row needs the older form: read the file through
a `<variable name="order" source="..." distribution="ordered"/>` in a generate whose
`count` is the number of data rows, and copy each column with a key script such as
`order.order_id` (`tests_ce/scenarios/s13_file_projection`).

Build, `authoring run` and smoke export write no file into the project. Only
`datamimic run datamimic.xml` writes a file target, to
`output/<exportUri>/<entity>.<ext>` beside `datamimic.xml`. Without `exportUri`
the directory is a new task id for each run. The example above writes
`output/order_report/order_report.json`. The complete project is
`tests_ce/scenarios/s22_file_filter`.

## Database sink table

`createTable="true"` on a `<generate>` with a database target creates the table
when it is missing. The project needs no DDL file and no `sqlite3` step. Write a
primary-key field as `<id>` and every other field as `<key>`; several `<id>` make
a composite key. The table name is `targetEntity` (else `type`, else `name`).

```xml
<setup rngSeed="59">
    <database id="ledger" dbms="sqlite" database="s59_ledger"/>
    <generate name="lines" count="6" target="CSV,ledger.upsert" targetEntity="journal_lines" createTable="true">
        <id name="line_id" generator="IncrementGenerator"/>
        <key name="account" values="('1000', '1200', '8400')"/>
        <key name="amount_cents" type="int" min="100" max="9999"/>
        <key name="posted_on" script="datetime.date(2026, 3, 1)"/>
        <key name="memo" script="None" type="string"/>
    </generate>
</setup>
```

```json
{
  "version": "5.0",
  "environment_bindings": [{"environment": "ledger", "family": "database"}],
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "lines"}, "count": 6},
    {"kind": "exact_count", "subject": {"kind": "declared_sink", "sink": {"kind": "database", "environment": "ledger", "entity": "journal_lines"}}, "count": 6}
  ]
}
```

The columns are the fields of the written rows. A key's `type=` sets the column
type. Without `type=`, the non-null values in the first page set it: `str`,
`int`, `float`, `bool`, `Decimal`, `date` or `datetime`. A column with only null
values, with mixed value types (for example `10` and `10.5`), or with another value type, fails with `I929`
and asks for `type=`.
The run creates the table once, before the first row. It never alters or drops a
table. A second run finds the table and upserts. An existing table that
lacks a written column or has another primary key fails with `I930` and the difference. Extra columns are allowed. A
later page that writes a field the table lacks (for example a key with a
`condition` that is false in the whole first page) also fails with `I930`: write
each field in the first page.

`createTable="true"` needs at least one direct-child `<id>` (`I929`). Without
`createTable`, or with `createTable="false"`, an `<id>` is a plain `<key>`. Build
derives a `unique` check on a single `<id>`; a composite key derives none, because
a `unique` expectation names one field. The generate needs a
`<database>` target with `dbms="sqlite"` or `dbms="postgresql"`, plain or with
`.upsert`; other dbms, `.update` and `.delete` fail with `I929`. It must be a root
generate, and `createTable` is not allowed with `clear` or
`drop`. The generate runs in one process. Build creates nothing: it shows the
CREATE TABLE statement in `planned_operations`, typed from the rows it captured
(at most `max_count`); the run types from its first page, so a field that first
appears after the captured rows is in the run's table only. `run-project` lists a `schema`
side effect (`ledger.journal_lines`) and needs `allow_side_effects`. The complete
project is `tests_ce/scenarios/s59_create_table`.

For exporter/replay verification add `"verification": {"smoke_export": true,
"deterministic_replay": true}` to `acceptance/build.json`. Build replays every
seeded model also without the request, under three other hash seeds. A target-isolated bounded
Build does not claim that an external database was written.

`max_count` limits the total captured product rows in one Build execution,
including nested products. Omit it: when every product has a literal count, Build
sets the limit to the declared total (at least 10, at most 2000). A source with a
literal count counts that count; a memstore readback without count counts the rows
of its literal producer. A nested product with a literal count multiplies the bound
of its parent, also of a source parent. A project with a file source without count, a script count
or a count range (`minCount`/`maxCount`) gets the limit 10; set `max_count` to the
total rows of all products. The products of every `<condition>` branch count in
full, so the derived limit can be higher than the rows of a run. A higher limit is
safe. Near the ceiling of 2000, the branches can cause a refusal: then set the
counts lower. Deterministic replay receives a fresh limit of the
same size; it verifies the same logical dataset. Export smoke reuses the first
capture and consumes no additional rows.

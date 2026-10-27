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

The producer identifier and consumer FK role pair makes readback integrity part
of the proof. Merely declaring a memstore target does not establish readback.

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

CSV columns arrive as strings: cast them in `where` and in scripts. `where` reads
one row: its columns, `this`, and the expression functions. It must not draw random
values, and it cannot read `parent.`, variables or setup names. `where` and `columns`
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

For exporter/replay verification add `"verification": {"smoke_export": true,
"deterministic_replay": true}` to `acceptance/build.json`. Build replays every
seeded model also without the request, under three other hash seeds. A target-isolated bounded
Build does not claim that an external database was written.

`max_count` limits the total captured product rows in one Build execution,
including nested products. Omit it: when every product has a literal count, Build
sets the limit to the declared total (at least 10, at most 1000). A source with a
literal count counts that count; a memstore readback without count counts the rows
of its literal producer. A nested product with a literal count multiplies the bound
of its parent, also of a source parent. A project with a file source without count, a script count
or a count range (`minCount`/`maxCount`) gets the limit 10; set `max_count` to the
total rows of all products. The products of every `<condition>` branch count in
full, so the derived limit can be higher than the rows of a run. A higher limit is
safe. Near the ceiling of 1000, the branches can cause a refusal: then set the
counts lower. Deterministic replay receives a fresh limit of the
same size; it verifies the same logical dataset. Export smoke reuses the first
capture and consumes no additional rows.

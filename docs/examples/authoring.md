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

`<generate source="fixtures/orders.csv">` copies every column of the file into
each row, also the columns that no `<key>` names. To keep only some columns, read
the file through a `<variable>` in source order and set `count` to the number of
data rows. Each `<key>` then copies one column. A `field_absent` expectation
proves that a column is not in the output.

```xml
<setup rngSeed="51110" defaultSeparator=",">
    <generate name="priced_orders" count="6" target="JSON" exportUri="priced_orders">
        <variable name="order" source="fixtures/orders.csv" distribution="ordered"/>
        <key name="order_id" script="order.order_id"/>
        <key name="total_cents" script="int(order.total_cents)"/>
    </generate>
</setup>
```

```json
{
  "version": "5.0",
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "priced_orders"}, "count": 6},
    {"kind": "field_absent", "subject": {"kind": "product", "product": "priced_orders"}, "field": "status"}
  ]
}
```

CSV columns arrive as strings: cast them in the script. A `count` above the data
rows cannot prove a complete capture, and Build rejects it. A file source has no
row filter: a `<condition>` decides which keys a row gets, not which rows exist.

Build, `authoring run` and smoke export write no file into the project. Only
`datamimic run datamimic.xml` writes a file target, to
`output/<exportUri>/<entity>.<ext>` beside `datamimic.xml`. Without `exportUri`
the directory is a new task id for each run. The example above writes
`output/priced_orders/priced_orders.json`. The complete project is
`tests_ce/scenarios/s13_file_projection`.

For exporter/replay verification add `"verification": {"smoke_export": true,
"deterministic_replay": true}` to `acceptance/build.json`. Build replays every
seeded model also without the request, under three other hash seeds. A target-isolated bounded
Build does not claim that an external database was written.

`max_count` limits the total captured product rows in one Build execution,
including nested products. Omit it: when every product has a literal count, Build
sets the limit to the declared total (at least 10, at most 1000). A source with a
literal count counts that count; a memstore readback without count counts the rows
of its literal producer. A project with a file source without count, a script count
or a count range (`minCount`/`maxCount`) gets the limit 10; set `max_count` to the
total rows of all products. Deterministic replay receives a fresh limit of the
same size; it verifies the same logical dataset. Export smoke reuses the first
capture and consumes no additional rows.

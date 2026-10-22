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

```xml
<setup rngSeed="7">
    <memstore id="store"/>
    <generate name="parents" count="2" target="store">
        <key name="id" generator="IncrementGenerator"/>
    </generate>
    <generate name="readback" source="store" type="parents" distribution="ordered">
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

For exporter/replay verification add `"verification": {"smoke_export": true,
"deterministic_replay": true}` to `acceptance/build.json`. A target-isolated bounded
Build does not claim that an external database was written.

`max_count` limits the total captured product rows in one Build execution,
including nested products. Deterministic replay receives a fresh limit of the
same size; it verifies the same logical dataset. Export smoke reuses the first
capture and consumes no additional rows.

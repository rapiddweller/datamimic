# Build transactions

Pass each JSON transaction to `datamimic authoring build -`. Persist the returned
`artifact.compiled_xml` only after `outcome: "ready"`; keep proof separately.
DM JSON is transient. XML retains runtime structure and seed, while each new Build
receives its expectations and roles again. Use the running schema for full fields.

## Nested foreign keys

Two parents, two child rows per parent. The child carries the real `parent.id`;
a randomly selected valid parent key does not establish per-parent cardinality.

```json
{
  "document": {"root": {
    "kind": "setup", "properties": {"rng_seed": 7}, "children": [
      {"kind": "generate", "properties": {"name": "parents", "count": 2}, "children": [
        {"kind": "key", "properties": {"name": "id", "generator": "IncrementGenerator"}},
        {"kind": "generate", "properties": {"name": "children", "count": 2}, "children": [
          {"kind": "key", "properties": {"name": "parent_id", "script": "parent.id"}}
        ]}
      ]}
    ]
  }},
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

```json
{
  "document": {"root": {
    "kind": "setup", "properties": {"rng_seed": 7}, "children": [
      {"kind": "memstore", "properties": {"id": "store"}},
      {"kind": "generate", "properties": {"name": "parents", "count": 2, "target": "store"}, "children": [
        {"kind": "key", "properties": {"name": "id", "generator": "IncrementGenerator"}}
      ]},
      {"kind": "generate", "properties": {
        "name": "readback", "source": "store", "type": "parents", "distribution": "ordered"
      }, "children": [
        {"kind": "key", "properties": {"name": "id", "script": "this.id"}}
      ]}
    ]
  }},
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

```json
{
  "document": {"root": {
    "kind": "setup", "properties": {"rng_seed": 7}, "children": [
      {"kind": "generate", "properties": {
        "name": "readings", "count": 2, "start": "2026-01-01T00:00:00",
        "end": "2026-01-01T03:00:00", "interval": "PT1H"
      }, "children": [
        {"kind": "key", "properties": {"name": "reading", "constant": "ok"}}
      ]}
    ]
  }},
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "readings"}, "count": 6}
  ]
}
```

For exporter/replay verification add `"verification": {"smoke_export": true,
"deterministic_replay": true}` to the transaction. A target-isolated bounded
Build does not claim that an external database was written.

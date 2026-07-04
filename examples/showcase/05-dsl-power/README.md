# How do I export one dataset to five formats, generate BLOBs, and enforce per-record invariants?

One seeded `<generate>` builds an employee roster and writes it to `mem`, CSV,
JSON, XLSX, and DbUnit in a single pass. Along the way it shows the DSL features
that turn a descriptor into a self-checking, review-ready artifact:

- **Computed count** — `count="{4 * 25}"` evaluates any python expression, not
  just a literal digit.
- **Binary / BLOB fields** — `type="binary" mimeType="image/png"` emits real
  bytes with a PNG magic-number header (MIME-sniffable). Seeded, so the bytes
  reproduce identically every run.
- **Field-level pseudonymization** — `converter="Substring(-4)"` keeps the last
  four card digits. `Substring` uses python-slice semantics; a negative index
  counts from the end.
- **Declarative invariants** — `<assert condition="…" message="…"/>` fails the
  whole run if any record violates it. Here one assert re-derives the tail from
  the source card, so the pseudonymization is proven, not assumed.
- **Explicit read/write entity** — `targetEntity="roster"` names the written
  entity (the files and the memstore key are `roster`, not `employees`); the
  second pass reads it back with the matching `sourceEntity="roster"`.
- **Output-directory prefix** — `exportUri="output"` prefixes every file target.

Output: `roster` (100 rows) as `output/roster.csv`, `.json`, `.xlsx`,
`.dbunit.xml`; plus `directory.json` derived from the rows read back.
`rngSeed="42"` makes the whole dataset reproduce identically on every run.

## Run it

```bash
datamimic run examples/showcase/05-dsl-power/datamimic.xml
# output lands in examples/showcase/05-dsl-power/output/
```

## Exporters & targets this example demonstrates

- **Multi-target in one write** — `target="mem,CSV,JSON,XLSX,DbUnit"` fans one
  generated entity out to five sinks; add or drop a format by editing the list.
- **XLSX** — spreadsheet read and write; on read the first row is the header.
- **DbUnit** — DbUnit dataset XML (`<dataset><roster .../></dataset>`); read a
  `.dbunit.xml` source the same way (`source="data/x.dbunit.xml"`).
- **`exportUri`** — a path prefix (relative to the descriptor) for every file
  target. It must be a path, not a URL, and may not traverse with `..`.
- **Binary in files vs DBs** — a database column stores the bytes natively; file
  targets render the byte repr, with the `image/png` header visible up front.

Database clients accept an operation suffix on the target — write with
`target="db"` (insert) or route rows to `target="db.upsert"`,
`target="db.update"`, or `target="db.delete"`:

```xml
<generate name="sync" source="mem" sourceEntity="roster" target="db.upsert"/>
```

## DB-backed features (shown here as snippets, not run offline)

These need a live database client, so they are documented rather than executed
in this self-contained example. All syntax is copied from the CE test suite.

- **Foreign keys from a real table** — `<reference>` with `distribution` and
  `cyclic` pulls existing keys (RDBMS sources only):

  ```xml
  <reference name="customer_id" source="sourceDB" sourceType="CUSTOMER"
             sourceKey="id" distribution="ordered" cyclic="true"/>
  ```

- **Run an assembled statement** — `<execute script="…">` runs SQL/DDL you built
  in python (a context value), with no string-concatenation in the XML:

  ```xml
  <execute type="sql" target="db" script="ddl_statement"/>
  ```

- **Dynamic include** — the `uri` is f-string-interpolated from context, so one
  descriptor pulls in the part chosen at runtime:

  ```xml
  <include uri="{model}"/>
  <include uri="{database}/shop.{database}.properties"/>
  ```

## Scope aliases

`this.field`, `parent.field`, and `root.field` address the current, enclosing,
and outermost record inside nested scopes — see
[01-banking-core](../01-banking-core/) for the worked two-hop foreign-key
example.

## What the same thing costs in hand-written code

Five exporters, base64/PNG framing for the blob, a slice helper for the last-4,
an assertion harness, and a seed nobody maintains — versus one `target=` list,
one `type="binary"`, one `converter=`, one `<assert>`, and one `rngSeed`.

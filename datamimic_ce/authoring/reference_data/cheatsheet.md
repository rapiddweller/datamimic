# DATAMIMIC DSL — Agent Cheatsheet (diagnostics v1)

DATAMIMIC descriptors are XML files (`datamimic.xml`) that declare data pipelines:
generate synthetic records, read/transform existing sources, and export to files,
databases, or in-memory stores. Deterministic by choice (`rngSeed`), reviewable,
re-runnable — lint with `datamimic_check`, execute safely with `datamimic_run`.

## Minimal descriptor

```xml
<setup rngSeed="1">
    <generate name="customers" count="100" target="JSON">
        <key name="id" generator="IncrementGenerator"/>
        <key name="age" type="int" min="18" max="99"/>
        <key name="segment" values="'retail','sme','corp'" weights="0.7,0.2,0.1"/>
    </generate>
</setup>
```

## Mental model

- `<setup>` is the root; top-level `<generate>` statements run in order.
- `<generate name= count=>` produces records; `<key>` defines one field,
  `<variable>` a per-record helper (not exported), `<nestedKey>`/`<list>`/`<array>`
  build nested structures.
- `source=` reads existing data (`.csv`, `.json`, `.xlsx`, `.xml`, `.dbunit.xml`,
  a `<memstore>` id, or a `<database>`/`<mongodb>` id).
- **`<generate>` vs `<iterate>`** — same engine element, different *intent*:
  use `<generate>` to CREATE records (write-only, or read-a-source-then-write);
  use `<iterate>` when the point is to READ/enrich an existing source in place.
  Same for `<id>` = a `<key>` that marks an identifier.
- `target=` writes: file exporters (`CSV`, `JSON`, `XML`, `XLSX`, `TXT`, `DbUnit`),
  `ConsoleExporter`, a `<memstore>` id (in-memory pipeline handoff), a client id, or
  `clientId.upsert` / `clientId.delete`. `exportUri=` prefixes the output directory.
- `script=` attributes evaluate **Python**: reference a field or `<variable>` by
  its **bare name** — `script="person.given_name"` or `script="age * 2"`. Do NOT
  write `__person__` there; the `__name__` form is *only* for string interpolation
  inside `string=`/`pattern=` (e.g. `string="__firstName___lastName__"`). A
  `<variable>` gives its result a dot-accessible object (`row['field']` fails,
  use `row.field`).
- **Scope aliases in scripts** (see `topic=context`): `this.field` (current record,
  == bare `field`; needed inside nested scopes), `parent.field` (enclosing
  `<generate>`/`<nestedKey>` — a child reading its parent, e.g. `parent.id`),
  `root.field` (outermost record).
- **Nested structures**: `<nestedKey type="dict">` builds one nested object from
  child `<key>`s; `<nestedKey type="list" minCount= maxCount=>` builds a list of
  them. With `source=`/`script=` a nestedKey instead reads/enriches existing data.
  Without `type` AND without `source`/`script` it builds nothing (DM216).
- **Entities**: 23 built-in domain entities (Person, Company, Address, Order,
  Patient, …) — `topic=entities` lists them, `topic=entities name=Person` lists
  its fields. `<variable name="p" entity="Person" dataset="DE" locale="de"/>` then
  `script="p.email"`.

## Top gotchas (each maps to a lint rule)

1. **Absent `distribution` = RANDOM, not source order** — add
   `distribution="ordered"` for file/table order. (DM301)
2. **random/cumulated/`unique` load the WHOLE source into memory**; only
   `ordered` reads page by page. (DM302)
3. **No `rngSeed` = every run differs** (by design). Seeded runs replay
   identically — and force single-process. (DM303, DM304)
4. `count` is digits or `{script}`; `count` XOR `minCount`/`maxCount`. Without
   `count`, a `source`/`script` must supply the rows. (DM212, DM201, DM202)
5. Every `<key>` needs exactly ONE value source: `type=` (+`min`/`max` or
   `minLength`/`maxLength`), `generator=`, `values=`, `constant=`, `script=`,
   `pattern=`, `source=`, or `string=`. `weights=` needs `values=`. (DM203)
6. `unique="True"` needs a finite pool (`values`/`source`) covering the count and
   only combines with random distribution. (DM204)
7. With `source=`: use `type=`/`sourceEntity=` OR `selector=`, not both. A
   MongoDB source needs one of them explicitly. `selector` without `count` only
   works on DB clients. (DM205, DM211)
8. Prefer native attributes over eval-strings:
   `type="int" min="1" max="9"` beats `generator="IntegerGenerator(min=1,max=9)"`;
   `minLength`/`maxLength` beat `StringGenerator(...)`. (DM310, DM311)
9. `<nestedKey cyclic="True">` requires a `count`; `<generate cyclic>` does not.
   (DM213)
10. Targets must exist: registry exporters, declared `<memstore>`/client ids, or
    `clientId.operation`. (DM401)

## Sources & credentials

- File sources resolve relative to the descriptor; type is inferred from the
  extension (`.dbunit.xml` before `.xml`).
- `<database id="db" system="postgresql" environment="local"/>` +
  `<mongodb id="mongo"/>` read credentials from `conf/{environment}.env.properties`
  with keys `{system}.{db|mongo}.{attr}` (e.g. `db.db.host`, `mongo.mongo.port`).
- Read with `source="db" selector="SELECT ..."` or
  `source="mongo" selector="find: 'coll', filter: {}"`; write with `target="db"`
  or `target="mongo.upsert"`.

## Control flow & structure

- `<condition><if condition="..."> ... </if><else-if/><else/></condition>` gate
  child statements per record; `<while>` loops; `<assert>` fails the run on a
  false condition.
- `<reference>` pulls foreign keys from another table/collection
  (`source= sourceType= sourceKey=`); `<field>` maps composite references.
- `<include uri="part.xml"/>` splits descriptors; `.properties` includes load
  key=value pairs at parse time.
- `<echo>` prints; `<comment>` is a no-op; `<memstore id>` declares an in-memory
  store; `<execute uri>` runs SQL/scripts against a client.
- Entity fields resolve case/underscore-insensitively (`givenName` == `given_name`).

## Verify loop for agents

1. `datamimic_reference topic=overview` (this sheet), `topic=element name=generate`
   for details, `topic=recipes` for starting points.
2. Draft the descriptor → `datamimic_check` → fix every diagnostic (each carries
   a fix_hint and rule id).
3. `datamimic_run` (safe: counts capped, targets neutralized, memstores kept) →
   inspect sample rows → iterate.
4. Ship the descriptor; run for real with `datamimic run path/to/datamimic.xml`.

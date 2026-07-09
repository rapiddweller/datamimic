# DATAMIMIC CE 4.0.0 Release Notes

DATAMIMIC CE 4.0.0 is the Benerator migration compatibility and reproducibility
release. Benerator CE remains maintained for existing projects; DATAMIMIC CE is
the modern continuation for new descriptor work and for teams moving long-lived
Benerator projects onto a Python-native, deterministic runtime. Descriptors from
Benerator-style projects can now be brought across with engine-level support for
native DB sequences, fixed-width files, a scriptable memstore, weighted state
machines, composite foreign keys, and the `<iterate>` / `<id>` / `<comment>`
vocabulary. Alongside that compatibility work, seeded runs are now
machine-independent and reproducible. This is a breaking change for 3.x seeded
golden files; see Migration Notes.

The release also adds XLSX, DbUnit, and fixed-width as first-class formats and
ships a DSL authoring toolchain: linting, dry-run execution, scaffolding, an MCP
server, and registry-derived reference data.

## Benerator Migration Compatibility

### `<iterate>`, `<id>`, and `<comment>`

`<iterate>` is an alias of `<generate>` for read/enrich workflows. `<id>` is an
identifier-oriented alias of `<key>`. `<comment>` is accepted as documentation
inside descriptors and has no runtime effect.

```xml
<iterate name="products" source="products.import.fcw" offset="2" distribution="ordered" target="db">
    <id name="id" database="db" generator="SequenceTableGenerator(sequence='zsv.t_product_id_seq')"/>
</iterate>
```

### Native DB sequences with explicit names

`SequenceTableGenerator(sequence='schema.seq_name')` binds to an explicitly named
Postgres sequence. Omit `sequence=` to keep the `{type}_{name}_seq` convention.
This also fixes a single-process execution path that could generate zero rows.

```xml
<generate name="orders" type="orders" count="1000" target="db">
    <key name="id" database="db" generator="SequenceTableGenerator(sequence='shop.order_id_seq')"/>
    <key name="status" values="'open','shipped','done'" weights="0.2,0.3,0.5"/>
</generate>
```

### Fixed-width column files

Benerator-style `.fcw` files are self-describing when read: the first line
carries the column specification. DATAMIMIC can now read and write fixed-width
files.

```text
# ean_code[13],name[30],price[8r0]
8000353006386Limoncello Liqueur            00009.85
```

```xml
<setup>
    <generate name="export" count="100" target="FixedWidth(columns='id[8r0],name[30]')" exportUri="out">
        <key name="id" generator="IncrementGenerator"/>
        <key name="name" pattern="[A-Z][a-z]{5,12}"/>
    </generate>

    <iterate name="reimport" source="products.import.fcw" target="ConsoleExporter"/>
</setup>
```

### `offset="N"` on file sources

`offset` skips the first N source rows. Count defaults, page windows, cyclic
wrap-around, and shuffled pools all operate on the post-offset region.

```xml
<iterate name="tail" source="rows.csv" offset="2" distribution="ordered" target="JSON"/>
<iterate name="wrapped" source="rows.csv" offset="2" cyclic="True" count="7" distribution="ordered" target="JSON"/>
```

### Scriptable memstore and client ids

Declared `memstore`, `database`, and `mongodb` ids are available in `script=` and
`<execute>` scopes, matching the common Benerator migration shape. Memstore
aggregation is lenient for non-numeric cells, and a whole entity bound into a
scalar DB/Mongo field is stringified deterministically.

```xml
<setup>
    <memstore id="mem"/>
    <database id="db" system="postgresql"/>

    <iterate name="orders" source="orders.csv" target="mem"/>

    <execute>
        total = mem.sumEntityColumn('orders', 'amount')
        mem.removeNotExistingIds('orders', 'customer_id', 'customers', db)
    </execute>

    <generate name="summary" count="1" target="JSON">
        <key name="order_count" script="mem.entityCount('orders')"/>
        <key name="total" script="total"/>
    </generate>
</setup>
```

### Weighted state machines

`<state-machine>` and `<transition>` generate reusable weighted state
progressions.

```xml
<setup rngSeed="1">
    <state-machine id="order_flow" start="created">
        <transition from="created" to="paid" weight="0.9"/>
        <transition from="created" to="cancelled" weight="0.1"/>
        <transition from="paid" to="shipped" weight="1"/>
    </state-machine>
    <generate name="orders" count="500" target="CSV">
        <key name="status" generator="order_flow"/>
    </generate>
</setup>
```

### Composite references, including MongoDB

Composite `<reference>` blocks map multiple target fields from the same source
row, including DB and MongoDB sources.

```xml
<generate name="order_items" count="5000" target="db">
    <reference name="order_ref" source="db" sourceType="orders" distribution="random">
        <field target="order_id" sourceKey="id"/>
        <field target="order_country" sourceKey="country"/>
    </reference>
    <key name="qty" type="int" min="1" max="9"/>
</generate>
```

### Value picks, counts, decimals, and numeric distributions

Native attributes now cover weighted values, unique value picks, `minCount` /
`maxCount`, exact decimals, Benerator-compatible bell-shaped numeric draws, and
deterministic numeric range sequences.

```xml
<generate name="txns" minCount="100" maxCount="200" target="CSV">
    <key name="channel" values="'web','pos','app'" weights="0.5,0.3,0.2"/>
    <key name="voucher" values="'A','B','C','D'" unique="True"/>
    <key name="amount" type="decimal" min="0.01" max="999.99" granularity="0.01"/>
    <key name="score" type="int" min="1" max="100" distribution="cumulated"/>
    <key name="sequence_id" type="int" min="1" max="100" distribution="step"/>
</generate>
```

Numeric range key distributions:

- `uniform`: default per-row random draw across the range.
- `cumulated`: per-row bell-shaped draw, mean at the midpoint.
- `step` / `increment`: finite ascending sequence, no wrapping.
- `shuffle`: deterministic strided walk, unique until exhausted.
- `wedge`: min, max, min+d, max-d, converging toward the middle.
- `bitreverse`: bit-reversed counter order over the range grid.
- `fibonacci` / `padovan`: recurrence values clipped to `[min, max]`.
- `randomWalk`: seeded bounded walk that starts at min and saturates at max.

Finite positional sequences are rejected under multiprocessing because each
worker would restart local iterator state and duplicate values. Use
single-process execution or a per-row distribution for those descriptors.

### Control flow and assertions

`<execute>`, `<while>`, and `<assert>` are supported for descriptor-local setup,
looping, and hard quality gates.

```xml
<setup>
    <execute>threshold = 42</execute>
    <generate name="rows" count="10" target="JSON">
        <key name="v" type="int" min="0" max="100"/>
        <assert condition="v >= 0"/>
    </generate>
</setup>
```

### Tolerant entity field access

Entity fields resolve case and underscore differences. For example,
`person.givenName` and `person.given_name` address the same field.

```xml
<generate name="people" count="100" target="CSV">
    <variable name="p" entity="Person" dataset="DE" locale="de"/>
    <key name="first" script="p.givenName"/>
    <key name="last" script="p.family_name"/>
</generate>
```

### Region-group datasets

Dataset groups such as `europe`, `western_europe`, `iberia`, and
`north_america` select an eligible country per row.

```xml
<generate name="addresses" count="1000" target="CSV">
    <variable name="addr" entity="Address" dataset="western_europe"/>
    <key name="country" script="addr.country_code"/>
    <key name="city" script="addr.city"/>
</generate>
```

### CSV compatibility

Padded or aligned CSV headers are trimmed on read, so `this.name` resolves even
when the file header contains surrounding whitespace. `.wgt.csv` weighted files
now accept an optional header row.

## Deterministic by Contract

`<setup rngSeed="N">` now reproduces identical output across machines and runs.
Literal generators, domain generators, DateTimeGenerator, weighted sources,
distributions, and null injection are seed-bound. Seeded descriptors run
single-process so page and worker boundaries cannot reorder output.

```xml
<setup rngSeed="42">
    <generate name="stable" count="1000" target="CSV">
        <variable name="p" entity="Person"/>
        <key name="name" script="p.name"/>
        <key name="joined" generator="DateTimeGenerator(min='2020-01-01', max='2025-12-31', input_format='%Y-%m-%d')"/>
    </generate>
</setup>
```

## Formats and Exporters

```xml
<setup>
    <iterate name="from_excel" source="input.xlsx" target="XLSX" exportUri="out"/>

    <iterate name="seeded" source="fixture.dbunit.xml" sourceEntity="customers" target="DbUnit"/>

    <generate name="upserts" count="100" target="db.upsert">
        <key name="id" generator="IncrementGenerator"/>
    </generate>

    <generate name="files" count="10" target="JSON">
        <key name="thumbnail" type="binary" minLength="64" maxLength="256" mimeType="image/png"/>
    </generate>
</setup>
```

## DSL Authoring and MCP

- `datamimic_check` lints descriptors with DM-rules and fix hints.
- Dry-run execution caps counts and neutralizes side-effecting targets.
- The MCP server exposes `generate`, `datamimic_check`, `datamimic_run`, and
  `datamimic_reference`.
- `datamimic_reference topic=distributions`, the MCP metadata, the capabilities
  manifest, and `reference_data/cheatsheet.md` document the full numeric
  sequence contract.

## Ergonomics and Fixes

- `this`, `parent`, and `root` script-scope aliases.
- Computed `count="{expr}"`.
- Dynamic `<include uri="{...}">`.
- `Substring(start[, end])` converter with Python slice semantics.
- Nested `<generate>` exports after its parent, preserving FK-safe write order.
- Data-source length cache keyed by `(statement, source)`.
- Mongo Decimal128 round-trips.
- Mongo CRUD collection routing fixes.
- Luhn-valid credit card numbers.
- Empty CSV files are empty sources, not crashes.

```xml
<generate name="parents" count="10" target="JSON">
    <key name="id" generator="IncrementGenerator"/>
    <generate name="children" count="3" target="JSON">
        <key name="parent_id" script="parent.id"/>
        <key name="code" script="parent.id" converter="Substring(-2)"/>
    </generate>
</generate>
```

## Migration Notes from 3.x to 4.0.0

1. Seeded output changes. A 3.x seeded run and a 4.0.0 seeded run with the same
   seed can produce different data. Every 4.0.0 run with the same model and seed
   is then stable. Re-baseline golden files.
2. Seeded runs are single-process. Drop the seed if parallel throughput matters
   more than replay.
3. Headerless `.wgt.csv` files are rejected as `<generate>` / `<iterate>`
   sources. A weighted file without column names is valid for per-field weighted
   picks, not row iteration.
4. Nested `<generate>` export order changed. Children now export after their
   parent.
5. `count=` above the source length warns and caps when `cyclic` is off.

Correct `.wgt.csv` usage:

```xml
<key name="status" source="status.wgt.csv" separator="|"/>

<iterate name="rows" source="status.wgt.csv" separator="|" target="JSON"/>
```

For row iteration, include a header line such as `value|weight`.

## Known Limitations

- `SequenceTableGenerator` is Postgres-only.
- An explicit `sequence=` name that does not exist is auto-created starting at 1.
  A typo can therefore create a fresh sequence instead of failing.
- `offset=` applies to file sources only. DB and memstore sources reject it; use
  selector-side skipping for those sources.
- JVM-specific custom script imports in migrated projects remain manual ports.

## Release Checklist

- [ ] Merge PR #204 into `development`.
- [ ] Confirm CI and quality gates are green on `development`.
- [ ] Tag `development` with `4.0.0`.
- [ ] Publish these notes with the GitHub release.
- [ ] Squash the release state into `main` according to `RELEASE.md`.

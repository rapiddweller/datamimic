# How do I branch records conditionally and generate evolving time-series data?

Two independent patterns in one descriptor.

**Conditional branching**: `<condition>` with `<if>` / `<else-if>` / `<else>`
routes every record based on its own generated fields. A loan application
with `score >= 700` gets `decision="approved"` and a low rate; a mid score
goes to manual review with a higher rate band; the rest are declined and
carry no rate field at all. The branch condition reads sibling keys directly.

**Time-series**: `<generate start="..." end="..." interval="PT30M">` iterates
over time instead of a count. `count="2"` means two series (here: two currency
pairs). Each tick exposes `ts.now`, `ts.step`, `ts.series` to `script=`, which
is enough for drift, seasonality, or regime logic in plain python. Total rows
= series x ticks: 2 x 17 half-hour ticks between 09:00 and 17:30.

## Run it

```bash
datamimic run examples/showcase/03-orchestration-timeseries/datamimic.xml
# output lands in examples/showcase/03-orchestration-timeseries/output/
```

## Semantic rules this example demonstrates

- `start`/`end`/`interval` are all-or-none; a partial set is a parse error.
- `count` in time-series mode is the number of series, not rows.
- `ts.*` is deterministic without a seed; the rngSeed only pins the random
  fields (score, rate_pct).
- An `<else>` branch that defines no `rate_pct` produces rows without that
  field: branches shape the record, not just its values.

## What the same thing costs in hand-written code

The decision table becomes nested ifs plus rate-band bookkeeping; the
time-series needs a datetime loop, series bookkeeping, and formatting. Both
drift from the spec the first time someone edits one side and not the other.

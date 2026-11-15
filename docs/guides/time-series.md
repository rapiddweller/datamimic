# Time-series generation with CE

This guide moved from the README.

## Time-series generation

Any `<generate>` becomes a time-series loop when given strict ISO 8601 `start`/`end`/`interval` attributes. Per iteration the script context exposes a `ts` namespace:

| Variable | Type | Meaning |
|---|---|---|
| `ts.now` | `datetime` | Current tick |
| `ts.step` | `int` | Position within one series (`0..N-1`) |
| `ts.series` | `int` | Which series this row belongs to (`0..count-1`) |

Output column names — including whether to even emit a timestamp or series-id column — are entirely the user's choice via `<key>`. The primitive is domain-agnostic; the same DSL covers IoT readings, financial ticks, log streams, smart meters, anything time-indexed.

```xml
<setup>
  <!-- Stock ticks: three symbols, 5-min interval, 30-min window (writes ticks.csv) -->
  <generate name="ticks" count="3"
            start="2026-01-01T09:30:00+00:00"
            end="2026-01-01T10:00:00+00:00"
            interval="PT5M"
            target="CSV">
    <key name="timestamp" script="ts.now.isoformat()"/>
    <key name="symbol"    script="['AAPL','MSFT','GOOG'][ts.series]"/>
    <key name="price"     script="100 + ts.step * 0.25"/>
  </generate>

  <!-- Sensor with diurnal seasonality, single series (count defaults to 1; writes readings.csv) -->
  <generate name="readings"
            start="2026-01-01T00:00:00+00:00"
            end="2026-01-08T00:00:00+00:00"
            interval="PT1H"
            target="CSV">
    <key name="timestamp" script="ts.now.isoformat()"/>
    <key name="value"     script="20 - 10 * math.cos(ts.now.hour * math.pi / 12)"/>
  </generate>
</setup>
```

Guarantees:

* **Prefix-stable by construction** — the first N ticks of series 0 are byte-identical regardless of total window length, because each row's `ts.now` is a pure function of `start + interval * step`.
* **Loop order is contiguous per series** — series 0's full sequence, then series 1's, etc. Makes downstream grouping trivial.
* **Strict ISO 8601** — `start`/`end` via `datetime.fromisoformat` (Z-suffix supported); `interval` via the [`isodate`](https://pypi.org/project/isodate/) library (`PT1H`, `PT15M`, `PT5S`, `P1D`, `P1W`, `P1DT12H`, fractional seconds for sub-second precision). Resolution: `PT0.001S` = 1 ms, `PT0.000001S` = 1 µs (Python `datetime.timedelta` microsecond floor; sub-µs intervals and constant-length-undefined units like months/years are rejected with a clear error).
* **`count` is orthogonal**, not overloaded — it means "outer-loop iterations of this `<generate>`" in **all** modes (same as nested `<generate count=…>`). In time-series mode each outer iteration is one series of N ticks, so total rows = `count × ticks_per_series`. Default `count="1"` keeps single-series fixtures terse.
* **Naming caveat** — a `<key name="ts">` output column would shadow the namespace (`current_product` overrides `current_variables` in script scope), and a `<variable name="ts">` is rejected at parse time. Use a different name, e.g. `timestamp` for the column.

Composes with the existing `<variable>` mechanism for multi-source merges (e.g. join each tick with a sensor-metadata CSV via `<variable source="meta.csv" cyclic="True">` inside the same `<generate>`), with `<key condition="...">` filtering, and with `<nestedKey>` sub-scopes — the `ts` namespace is visible everywhere a `<key script>` runs. See `tests_ce/integration_tests/test_timeseries/` for committed DSL fixtures + proofs (including pagination invariance).

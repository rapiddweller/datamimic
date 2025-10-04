# DateTime Generator: Weighted, Deterministic, and DSL Sugar

The `DateTimeGenerator` produces datetimes within an optional range, with support for:

- Weighted hours/minutes/seconds and month/day selection
- Deterministic sequences via `seed`
- Boundary-safe sampling (never exceeds `[min, max]` down to seconds)
- User-friendly DSL sugar for months, weekdays, day-of-month and time presets

## Quick Examples (XML DSL)

- Uniform within a window:
  - `DateTimeGenerator(min='2024-01-01 00:00:00', max='2024-12-31 23:59:59', random=True)`

- Deterministic:
  - `DateTimeGenerator(random=True, seed=42)`

- Time weights only (uniform date):
  - `DateTimeGenerator(random=True, hour_weights='[0.2]*6 + [0.02]*18')`

## DSL Sugar

You can express date filters and time patterns without writing full weight arrays.

### Months

- Include or exclude sets:
  - `months='3,7-9'` (March, July–September)
  - `months_exclude='2,4'` (exclude Feb and Apr)
- Quarter tokens:
  - `months='Q1'` → Jan–Mar
  - `months='Q2,Q4'` → Apr–Jun and Oct–Dec

### Weekdays

Accepts names, ranges, and presets. Monday=0, Sunday=6.

- Names/ranges:
  - `weekdays='Mon-Fri'`
  - `weekdays='Fri-Mon'` (wrap-around)
- Presets (case-insensitive):
  - `weekdays='Weekend'` → Sat, Sun
  - `weekdays='Weekdays'` / `Business` / `Workdays` → Mon–Fri
  - `weekdays='All'` → every day

### Day-of-Month (DOM)

- Specific days/ranges:
  - `dom='1-5,15,31'`
- Last day of the month:
  - `dom='last'`

### Time Presets and Granularity

- Hours:
  - `hours_preset='office'` → 09–17 weighted high
  - `hours_preset='night'` → 22–05 weighted high
  - `hours_preset='flat'` → no hour bias (uniform)
- Minute/Second tick spacing:
  - `minute_granularity=15` → 0, 15, 30, 45 only
  - `second_granularity=10` → 0, 10, 20, 30, 40, 50 only

## Exact Boundaries

If `min`/`max` constrain the first/last day, hours/minutes/seconds are sampled only within valid ranges for those edge dates. This prevents out-of-bounds times.

## Determinism

Provide `seed` to get reproducible sequences (same inputs → same outputs).

```python
from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

g1 = DateTimeGenerator(random=True, seed=123)
g2 = DateTimeGenerator(random=True, seed=123)
assert g1.generate() == g2.generate()
```

In domain generators, prefer centralizing date selection behind a helper (e.g., `generate_order_date()`), so models remain pure and tests can inject a seeded RNG at the generator level.

## Validation

The generator validates:
- Weight vector lengths (24/60/60/12/7/31)
- Non-negative values and non-zero sum
- Sugar specs that yield at least one eligible date; otherwise a clear error is raised

## Demo Snippets

See `datamimic_ce/demos/demo-datetime/1_datetime_generator.xml` for ready-to-run examples using the DSL sugar and weights.

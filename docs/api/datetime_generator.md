# DateTimeGenerator – Reference and Usage

The `DateTimeGenerator` produces datetime values for your keys/variables. It supports fixed values, uniform or weighted random sampling, strict min/max bounds, deterministic seeding, and user‑friendly DSL sugar.

See ready‑to‑run demos: datamimic_ce/demos/demo-datetime/1_datetime_generator.xml

## Modes

- Custom value: `value='<date string>'` parsed with `input_format`
- Random window: `random=True` with optional `min`/`max`
- Current time: no params → uses `datetime.now()`

## Core Parameters

- `min` / `max` (str): Optional bounds. Parsed using `input_format` (default `%Y-%m-%d %H:%M:%S`).
- `value` (str): Fixed datetime string using `input_format`.
- `random` / `random_mode` (bool): Enable random sampling. `random_mode` is the clearer alias.
- `input_format` (str): Parse format for `min`, `max`, `value`. Default `%Y-%m-%d %H:%M:%S`.
- `seed` (int): Deterministic RNG seed. Same seed + same params → same sequence.

Bounds are respected down to the second. If the sampled day equals the min/max day, hour/minute/second are clamped into the legal sub‑range so results never fall outside `[min, max]`.

## Time Weights (intra‑day)

- `hour_weights` (list[24] of float)
- `minute_weights` (list[60] of float)
- `second_weights` (list[60] of float)

Rules:
- Length must match (24/60/60). Values non‑negative and sum > 0 when provided.
- If time weights are omitted, distribution is exactly uniform within the window.

## Day Selection Weights (inter‑day)

- `month_weights` (list[12] of float)
- `weekday_weights` (list[7] of float) – Monday=0, Sunday=6
- `dom_weights` (list[31] of float) – day‑of‑month 1..31

How it works:
- The generator builds a distribution across all eligible days in the `[min, max]` window.
- Each day’s weight = month_weight × weekday_weight × dom_weight.
- A month is drawn proportional to the sum of its days’ weights; then a day is drawn using that month’s day weights.

Validation:
- Correct lengths, non‑negative numbers, and non‑zero total weight are enforced.
- If no day is eligible → clear ValueError.

## DSL Sugar (friendly shortcuts)

Instead of supplying raw weight arrays, you can use compact sugar attributes. Sugar is applied only when explicit weights for that dimension are not provided.

- `months` / `months_exclude`: restrict months
  - Examples: `months='3,7-9'`, `months_exclude='2,4'`
  - Quarters supported: `months='Q1'` (Jan–Mar), `months='Q2,Q4'` (Apr–Jun, Oct–Dec)
- `weekdays`: names, ranges, presets (Mon=0, Sun=6)
  - Names/ranges: `weekdays='Mon-Fri'`, `weekdays='Fri-Mon'`
  - Presets: `weekdays='Weekend'`, `weekdays='Weekdays'`/`Business`/`Workdays`, `weekdays='All'`
- `dom`: day‑of‑month
  - Examples: `dom='1-5,15,31'`, `dom='last'` (last day of each month)
- `hours_preset`: `office` (09–17 high), `night` (22–05 high), `flat` (no bias)
- `minute_granularity` / `second_granularity` (int)
  - Keeps only ticks divisible by granularity (e.g., `15` → 0,15,30,45)

Notes:
- Sugar composes with bounds. If both `months` and `month_weights` are given, `month_weights` take precedence.
- DOM `last` is resolved per month; other DOM filters still apply.

## XML Examples

Uniform window:

<setup>
  <generate name="uniform" count="3">
    <key name="dt" generator="DateTimeGenerator(min='2024-01-01 00:00:00', max='2024-12-31 23:59:59', random=True)"/>
  </generate>
</setup>

Office hours at 15‑minute and 10‑second ticks:

<setup>
  <generate name="office" count="3">
    <key name="dt" generator="DateTimeGenerator(min='2024-04-01 00:00:00', max='2024-04-30 23:59:59', random=True, hours_preset='office', minute_granularity=15, second_granularity=10, seed=7)"/>
  </generate>
</setup>

Month/weekday/DOM sugar:

<setup>
  <generate name="filters" count="3">
    <key name="march" generator="DateTimeGenerator(min='2024-01-01 00:00:00', max='2024-12-31 23:59:59', random=True, months='Q1')"/>
    <key name="mondays" generator="DateTimeGenerator(min='2024-01-01 00:00:00', max='2024-01-31 23:59:59', random=True, weekdays='Mon')"/>
    <key name="last_day" generator="DateTimeGenerator(min='2024-01-01 00:00:00', max='2024-12-31 23:59:59', random=True, dom='last')"/>
  </generate>
</setup>

See also: datamimic_ce/demos/demo-datetime/1_datetime_generator.xml

Weighted sampling with month/hour/minute/second weights:

<setup>
  <generate name="dateTimeGenerator" count="3" target="ConsoleExporter">
    <key name="biased_datetime"
         generator="DateTimeGenerator(
           min='2020-02-01 0:0:0',
           max='2025-07-31 0:0:0',
           month_weights='[0.5] * 2 + [1] * 3 + [0.8] * 3 + [1] * 3 + [0.5]',
           hour_weights='[0.6]*6 + [0.3]*16 + [0.1]*2',
           minute_weights='[1 if m in (0,15,30,45) else 0 for m in range(60)]',
           second_weights='[1]+[0]*59'
         )"/>
  </generate>
</setup>

Note: ensure `month_weights` length equals 12; the above pattern is 12 elements.

## Python API Examples

from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

# Deterministic window, weekends only
gen = DateTimeGenerator(
    min="2024-01-01 00:00:00",
    max="2024-01-31 23:59:59",
    random=True,
    weekdays="Weekend",
    seed=42,
)
print(gen.generate())

# Time weights only, uniform date
gen = DateTimeGenerator(random=True, hour_weights=[0.2]*6 + [0.02]*18, seed=1)
print(gen.generate())

## Formatting in Keys/Variables

To convert formats in XML, use `inDateFormat` and `outDateFormat` on the `<key>` or `<variable>` (conversion is outside the generator itself). See tests_ce/functional_tests/test_datetime/functional_test_datetime.xml:1.

## Error Handling

- Invalid lengths, negative weights, or all‑zero weights → ValueError with a clear message.
- Sugar that yields no eligible days in the window (e.g., `months='2'` with a January‑only range) → ValueError.

## Determinism & Performance

- Uses a private RNG with optional `seed` for reproducibility.
- O(1) per sample; day distributions built lazily when any day‑level weighting/sugar is provided.

## Demos & Tests

- Demo XML: datamimic_ce/demos/demo-datetime/1_datetime_generator.xml
- Functional tests: tests_ce/functional_tests/test_datetime/test_datetime.py

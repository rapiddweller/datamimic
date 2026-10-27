# e07 order report

Hidden from the subject. The subject gets `prompt.md` and `fixtures/` only.
The case reads two CSV files, joins them, applies three rules and writes one JSON dataset.
`fixtures_changed/` holds other customers and orders with the same columns. The oracle runs the project with them too, so typed rows fail.

## Prompt to check

| Prompt requirement | Check |
|---|---|
| the project is ready (brief) | `build_ready` |
| a JSON file for `order_report`, exact field set, all rules below | `output_rows:order_report:fixtures`, `output_rows:order_report:fixtures_changed` |
| only orders with `amount_cents` 1000 or more (threshold) | both `output_rows` |
| `customer_name` from `customers.csv`, `UNKNOWN` for an unknown customer (lookup with a default) | both `output_rows` |
| `net_cents`: 10 % for `GOLD`, 5 % for `SILVER`, 0 otherwise, discount rounded down | both `output_rows` |
| `campaign` `YES` from 2026-03-01 to 2026-03-31, both days included (date window) | both `output_rows` |
| do not change the two files | `fixtures_unchanged` |
| seed `40961` | `seed_is`; `repeatable` |

`output_rows` compares the rows with their JSON types and ignores the row order. A missing or extra field fails it.

## Boundary rows

Each fixture set has a row on each side of each rule:

| Rule | `fixtures/` | `fixtures_changed/` |
|---|---|---|
| threshold 1000 | 999 (out), 1000 (in), 1001 (in) | 999 (out), 1000 (in), 1001 (in) |
| campaign window | 02-28, 03-01, 03-31, 04-01 | 02-28, 03-01, 03-31, 04-01 |
| lookup default | C-109, C-110 | C-298, C-299 |
| one customer, several orders | C-101, C-102, C-104 | C-201, C-202, C-204 |
| tiers | GOLD, SILVER, BRONZE, empty | GOLD, SILVER, BRONZE, empty |
| rounding | 1999 GOLD: 1800, not 1799 | 2999 GOLD: 2700, not 2699 |

The two sets keep different numbers of orders (12 and 10) and different numbers of kept orders (9 and 8).

## Reference

A file source has no row filter, and a `<generate source=...>` copies every column. So the reference reads both files into one row of `report_input` (`storage="data"`).
`order_report` is nested in it: one row for each kept order (`count="{len(kept)}"`), and one key for each report field.
`report_input` has `target="ConsoleExporter"`: Build needs a target on it when the document has a file exporter (DM407), and this one writes no file.
Build captures 10 rows, in the cap of 1000. The dynamic count stops Build from deriving the row total, so the reference sets `max_count`.

## Equivalence classes

| Class | Variant in `test_authoring_eval.py` |
|---|---|
| valid | `reference/` with both fixture sets |
| threshold min - 1, min, min + 1 | the fixture rows 999, 1000, 1001; `threshold_excludes_1000` |
| no filter, flat copy | `no_threshold`, `_CHEATS` `e07-flat_copy` |
| duplicate: each order twice | `each_order_twice` |
| type: CSV text compared as text | `threshold_compared_as_text` |
| missing customer | `other_default_name` |
| empty tier, other tier, silver | the fixture rows; `silver_without_discount` |
| rounding | `net_rounded_down_instead_of_the_discount` |
| window first and last day | `campaign_without_its_first_day`, `campaign_without_its_last_day` |
| field set: extra, missing, source columns | `extra_field`, `missing_field`, `source_columns_in_the_output` |
| no file | `no_json_file` |
| hard-coded answer | `_CHEATS` `e07-typed_rows` (fails `fixtures_changed` only) |
| order: shuffled read | `orders_read_shuffled` (passes) |
| edited input | `edited_fixture` |
| seed and hash order | `missing_seed`, `wrong_seed`, `hash_ordered_campaign` |

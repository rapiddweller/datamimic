# How do I assemble one dataset from a CSV, generated fields, and a lookup table?

Drive the outer `<iterate>` with the CSV (every source column flows into the
row and is scriptable), enrich with generated fields (Person entity, weighted
values), and join static reference data with an inline python dict in
`script=`. The nested `<generate>` runs once per CSV row, so every customer
carries the real `branch_id` and `city` of its branch. The join cannot drift
because it never happens: children are generated inside their parent.

## Run it

```bash
datamimic run examples/showcase/02-multi-source-assembly/datamimic.xml
# output lands in examples/showcase/02-multi-source-assembly/output/
```

## Semantic rules this example demonstrates

- `<iterate source="data/branches.csv" separator="|">` reads the file relative
  to the descriptor; `distribution="ordered"` keeps source order and reads
  page by page.
- CSV columns arrive as strings. Cast before arithmetic:
  `script="int(parent.branch_id)"`.
- Inside a nested scope, record-local names need `this.`: sibling keys
  (`this.branch_id`) and variables (`this.person.name`) alike.
- `script=` is plain python: `{'retail': 4.90, 'business': 12.90}[this.segment]`
  is a complete lookup join, no extra source file needed.

## What the same thing costs in hand-written code

CSV parsing, type casting, a join dict, per-branch grouping, and name
generation are five separate concerns in a script. Here the CSV IS the loop,
the join is the nesting, and the enrichment is three declarative lines.

# How do I generate a multi-table banking dataset with referential integrity?

Nest `<generate>` blocks. The inner block runs once per outer record, so every
child row is born holding its parent's real key: accounts reference their
customer via `parent.customer_id`, transactions reference their account via
`parent.account_id` and the owning customer via `root.customer_id` (a two-hop
foreign key). A second pass then reads the accounts back from the `<memstore>`
and derives one statement per real account row.

Output: `customers` (40), `accounts` (1..3 per customer), `transactions`
(2..6 per account), `account_statements` (one per account). Every foreign key
resolves; `rngSeed="42"` makes the whole dataset reproduce identically on
every run.

## Run it

```bash
datamimic run examples/showcase/01-banking-core/datamimic.xml
# output lands in examples/showcase/01-banking-core/output/
```

## Semantic rules this example demonstrates

- `parent.field` reads the enclosing record; `root.field` reads the outermost
  one (the two-hop FK).
- Inside a nested `<generate>`, an earlier sibling key must be addressed as
  `this.field`; bare names only resolve at the top level.
- `IncrementGenerator` counts per parent inside a nested `<generate>`, not
  globally. Compose globally unique child ids from the parent key plus the
  local sequence (`parent.customer_id * 10 + this.account_no`).
- A `<memstore>` target keeps every generated table queryable by later
  `<generate source=...>` passes in the same descriptor.

## What the same thing costs in hand-written code

A faker script needs id bookkeeping for three tables, explicit FK plumbing,
a second pass over accounts, and a seed discipline nobody maintains. Typical
result: orphaned transactions and a dataset that changes on every run. Here
the FK plumbing is the nesting itself, and the seed is one attribute.

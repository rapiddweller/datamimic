# Amendment 13: unseeded descriptor acceptance

Date: 2026-09-24. Alex approved structural comparison for unseeded runs.

## Decision

- A root `rngSeed` run must retain exact captured rows and normalized exported
  content. Without a root seed, random values and genuinely dynamic counts need
  not equal another run.
- For unseeded runs, fixed descriptor counts remain exact. A dynamic count must
  satisfy its descriptor-defined range and same-run relationships (for example,
  `teCount == totalCount == len(te)`). Outcomes, product names, record/field
  structure, optionality, types, and export format/schema must remain compatible.
- `unknown`, empty capture, or an unexamined output file is not proof of
  structural parity. Such paths stay `UNVERIFIED` until a stronger oracle or an
  explicit path-level test establishes the relevant facts.

## Why

The frozen protocol compared row counts literally even for unseeded counts
drawn by the descriptor. The unchanged Step-0 program produces different valid
counts on repeats of `test_memstore_sum_and_count.xml`. Literal cross-run count
equality would reject valid behavior; dropping count checks entirely would
miss broken within-run relationships.

This changes the acceptance interpretation, not production code, XML, or the
architecture contract. The existing comparator does not yet implement the
whole decision; its current result cannot be promoted to a behavioral pass.

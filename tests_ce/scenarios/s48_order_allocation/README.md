# S48 order allocation (X4)

This project allocates stock lots to eight orders for one week. A lot has a quantity and an expiry date. An order
ships on one day. All names and data are synthetic.

## Run the tests

```bash
pytest tests_ce/scenarios -q -k s48
datamimic authoring build tests_ce/scenarios/s48_order_allocation
```

The tests live in `tests_ce/scenarios/test_scenarios.py`. They Build, run and replay the project, and Build each negative.

## Process

```text
data/entity/*, conf/* ──> 10 prepare ──> 20 eligibility ──> 30 allocate ──> 90 validate input ──> 91 validate output ──> 93 export
                          typed tables    A3, A1             search A2,A4,A5  input values          A1..A5 again          CSV files
```

| Step | File | Purpose |
|---|---|---|
| 10 prepare | `model/10_prepare.xml` | Read each data file and give each column its type. |
| 20 eligibility | `model/20_eligibility.xml` | For each order, decide which lots may serve it: the product (A3) and the expiry date (A1). |
| 30 allocate | `model/30_allocate.xml` | Search for one allocation and keep the evidence of each decision. |
| 90 validate input | `delivery/90_validate_input.xml` | Measure lot and order quantities. Build compares them. |
| 91 validate output | `delivery/91_validate_output.xml` | Measure the allocation against every rule again, from the data. |
| 93 export | `delivery/93_export.xml` | Read each product back from the store and write it to CSV. |

The checks are a gate in Build only. A plain `datamimic run` exports an allocation that breaks a rule and ends with
exit code 0. Run only a project whose files Build proved. There is no cleanup step: a CSV export writes a new output
directory for each run.

## Files

| File | Owner of |
|---|---|
| `conf/policy.properties` | `max_lots_per_order` and `search_budget`. A value that is not a whole number stops step 10. |
| `data/entity/products.ent.csv`, `customers.ent.csv` | The products and the customers. |
| `data/entity/lots.ent.csv` | The stock lots: product, quantity and the last day on which the lot may ship. |
| `data/entity/orders.ent.csv` | The orders: product, quantity, ship date, and `allow_partial` (`yes` or `no`). |
| `lib/allocation_search.scr.py` | The global search `allocate_orders`. |
| `acceptance/build.json` | The roles, the input and rule expectations, and the caller's edge controls. |

## Rules

| Rule | Decided in | Checked in the output |
|---|---|---|
| A1 the expiry date is a valid ship day, the day after is not | the `excluded_by` key of `lot_decisions` in step 20 | `days_to_expiry >= 0` on `allocation_checks` |
| A2 no lot ships more than its quantity | `fill` in `allocate_orders` | `lot_allocated <= lot_quantity` |
| A3 a lot serves only its product | the `excluded_by` key in step 20 | `same_product` |
| A4 an order without `allow_partial` is filled completely; a partial order ships all valid stock | `solve` and the partial pass | `allow_partial == 'yes' or backordered == 0`, `backordered == 0 or valid_left == 0 or lots_used == max_lots` on `order_checks` |
| A5 an order uses at most `max_lots_per_order` lots | `sets` and the partial pass in `allocate_orders` | `lots_of_order <= max_lots`, read from the policy; the caller requirement `max_lots_per_order <= 2` on `policy`; the pin that O8 ships 6 of 8 |

The output checks read the orders, the lots and the allocation again. They do not read the eligibility step or the
search evidence, so a defect in either is caught.

## Search

`allocate_orders` fills the orders that do not allow a partial shipment first (ship date, then id). It is a
depth-first search with backtracking.

1. For each order, try the lot sets of at most `max_lots_per_order` lots, earliest expiry first. A set must hold the
   whole quantity.
2. After each choice, check that every later order still has a lot set. If not, undo the choice (a backtrack).
3. Count each tried lot set as one step. Stop at `search_budget` steps.
4. Then ship the remaining valid stock to the partial orders, in ship date order.

With the data of this project the search needs 5 steps and 1 backtrack; the caller requirement `backtracks >= 1` pins it.

| `outcome` | `search_complete` | Meaning |
|---|---|---|
| `solved` | true | Every order is filled. |
| `infeasible` | true | No allocation exists. The message names the cause. |
| `budget_exhausted` | false | The search stopped at `search_budget` steps. This does not prove that no allocation exists. |

## Edge controls

| Edge | Data | Control |
|---|---|---|
| A lot ships on its expiry date | O4 ships on 2026-03-05, L5 expires on 2026-03-05 | allocation `A04` has `days_to_expiry == 0` |
| A lot does not ship the day after | O6 ships on 2026-03-06, L6 expired on 2026-03-05 | O6 ships 0 and has 4 back-ordered |
| A partial order ships what is left | O7 asks 4 of P2, 2 are left after O5 | O7 ships 2 and has 2 back-ordered |
| The lot limit stops a partial order | O8 asks 8 of P3; three lots hold 3 each | O8 ships 6 from two lots and has 2 back-ordered; the third lot has reason `A5` |

## Negatives

Each negative is one text patch in `scenario.json`. Build rejects the variant with a `row_condition` that names the rule.

| Negative | What breaks |
|---|---|
| `a1_expiry_exclusive`, `a1_expiry_ignored` | The expiry date is read as exclusive, or ignored. |
| `a3_product_ignored` | A lot of another product may serve an order. |
| `a2_oversell` | An allocation line takes the whole order from a lot. |
| `a4_partial_ships_nothing` | A partial order ships nothing. |
| `a5_lot_limit_raised` | `max_lots_per_order` is 3: O8 ships all 8 from three lots, and the O8 pin fails. The caller also requires at most 2. |
| `a5_search_ignores_limit` | The partial pass takes any number of lots: O8 uses three and `lots_of_order <= max_lots` fails. |
| `infeasible_three_lots_needed` | O8 does not allow a partial shipment: it needs three lots and no allocation exists. |
| `evidence_reason_unnamed` | The evidence leaves the reason word of a used lot empty. |
| `infeasible_order_too_large` | O4 asks 40 and no lot set holds it. |
| `budget_exhausted` | `search_budget` is 2. |
| `policy_not_whole` | `max_lots_per_order` is `two`; step 10 stops (`child_execution`). |
| `lot_without_quantity` | A lot has quantity 0. |

## Known limits

- Build reports two DM214 warnings: the `nestedKey` elements `lot_decisions` and `lots` have no `defaultValue`. A
  fallback would hide a failure in the decision evidence.
- A product that goes to the store needs a readback and an identifier, so step 93 exports each of them. The nested key of `order_decisions` is `lot_reasons`: the name `lots` would hit the product `lots`.
- The search tries lot sets by expiry order only. It is exact, but it grows with more orders and lots.

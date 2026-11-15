# S49 ledger postings (X5)

This project posts the invoices and payments of one month to a small ledger. Each invoice makes a journal entry
(receivable, revenue, tax). Each payment is split over the open invoices of its customer and makes a journal entry
(cash, receivable). The rules hold across the lines of an entry, across all lines of an account, and across the whole
ledger. All names and data are synthetic.

## Run the tests

```bash
pytest tests_ce/scenarios -q -k s49
datamimic authoring build tests_ce/scenarios/s49_ledger_postings
```

The tests live in `tests_ce/scenarios/test_scenarios.py`. They Build, run and replay the project, and Build each negative.

## Process

```text
data/entity/*, conf/* ──> 10 prepare ──> 20 amounts ──> 30 allocate ──> 40 post ──> 90 validate input ──> 91 validate output ──> 93 export
                          typed tables    tax, gross     split payments   entries     input values          L1..L8 again          CSV files
                                          (L7)           (L6)             and lines
```

| Step | File | Purpose |
|---|---|---|
| 10 prepare | `model/10_prepare.xml` | Read each data file and give each column its type, and read the period close date. |
| 20 amounts | `model/20_amounts.xml` | Compute the tax of each invoice, rounded half up, and its gross amount. |
| 30 allocate | `model/30_allocate.xml` | Split each payment over the open invoices of its customer, to the cent. |
| 40 post | `model/40_post.xml` | Write one journal entry for each invoice and payment, with its lines. |
| 90 validate input | `delivery/90_validate_input.xml` | Measure invoice and payment values. Build compares them. |
| 91 validate output | `delivery/91_validate_output.xml` | Measure the postings against every rule again, from the data. |
| 93 export | `delivery/93_export.xml` | Read each product back from the store and write it to CSV. |

The checks are a gate in Build only. A plain `datamimic run` exports postings that break a rule and ends with exit
code 0. Run only a project whose files Build proved. There is no cleanup step: a CSV export writes a new output
directory for each run.

## Files

| File | Owner of |
|---|---|
| `conf/policy.properties` | `period_close`, the last day on which a line may be posted. A value that is not an ISO date stops step 10. |
| `data/entity/accounts.ent.csv` | The accounts: kind, normal side, currency, the days it is open, and `allow_negative`. An empty `closed_on` is an account that is not closed. |
| `data/entity/customers.ent.csv`, `invoices.ent.csv`, `payments.ent.csv` | The customers, the invoices (net amount, tax rate in basis points, date) and the payments. All amounts are whole cents. |
| `lib/payment_allocation.scr.py` | The global split `allocate_payments`. |
| `acceptance/build.json` | The roles, the input and rule expectations, and the caller's edge controls. |

## Rules

| Rule | Decided in | Checked in the output |
|---|---|---|
| L1 each entry balances | the lines of step 40 | `entry_debits == entry_credits` on the line checks |
| L2 the account is open on the posting day; the closing day is open | step 40 and `accounts.ent.csv` | `days_since_open >= 0 and (days_to_close == None or days_to_close >= 0)` |
| L3 a line has one positive side | step 40 | `one_sided` |
| L4 the currency of a line is the currency of its account | step 40 | `currency_matches` |
| L5 the balance of an account is not below zero on its normal side | the order of the lines | `allow_negative == 'yes' or balance_after >= 0` |
| L6 a payment is split in proportion to the open amounts, to the cent; it pays only invoices dated on or before it | `allocate_payments` | `payment_allocated == payment_amount`, `invoice_allocated <= invoice_gross`, `days_after_invoice >= 0` on `allocation_checks` |
| L7 the tax is rounded to the nearest cent, half up; gross is net plus tax | step 20 | `tax_error_tenth_basis <= 5000 and gross_is_net_plus_tax`; the pin `tax_cents == 200` for I1 |
| L8 no line after the period close; the close day is open | step 40 and `conf/policy.properties` | `days_to_period_close >= 0` |

The trial balance (`total_debits == total_credits` on `ledger_checks`) follows from L1 and is measured on all lines.
The output checks read the invoices, the payments, the accounts and the lines again, not the allocation evidence.

## Split

`allocate_payments` handles the payments by date, then id. For each payment it takes the open invoices of the customer
that are dated on or before the payment day. Each invoice gets `floor(payment x open / total open)` cents. The cents
that are left go to the largest fractional parts, one each, ties by invoice id (`split_evidence` shows `floor_cents`
and `extra_cent`). A payment above the total open amount is `infeasible`: nothing is allocated, and `plan.message`
names the payment.

There is no search budget: the split is a closed form and has no backtracking, so `search_complete` has no meaning here.

## Edge controls

| Edge | Data | Control |
|---|---|---|
| A rounding cent goes to the largest remainder | P1 pays 3000 over 1250 and 3966 open: 718.9 and 2281.1 | AL01 and AL02 add up to 3000; `AL01` gets the extra cent |
| The tax rounds half up | I1: 1050 x 19 % = 199.5 | `tax_cents == 200` |
| The closing day of an account is open | A310 closes on 2026-03-31; I3 posts its tax that day | line `JE-I3/3` has `days_to_close == 0` |
| The close day of the period is open | `period_close` is 2026-03-31 | line `JE-I3/3` has `days_to_period_close == 0` |
| A payment pays an invoice of its own day | P3 pays I3 on 2026-03-31 | allocation `AL06` has `days_after_invoice == 0` |
| A payment that exactly equals the open amount | P2 pays the whole I4 | the payment is allocated in full |

## Gaps in the expectation kinds

The checks are products that measure a value. A rule that crosses rows or tables cannot be one expectation today:

- No expectation sums or counts over a group (entry balance, account balance, trial balance). The check product
  measures the sum in a key and a `row_condition` compares it.
- A `row_condition` compares numbers, text and booleans. It does not compare dates, so the checks measure days.
- A `row_condition` has no functions such as `str`. The checks use arithmetic.
- No expectation reads a running order. `balance_after` sums the earlier lines of the account in each row.
- No composite uniqueness of `(entry_id, line_no)`; `line_id` holds both and is unique.

## Negatives

Each negative is one text patch in `scenario.json`. Build rejects the variant with a `row_condition` that names the rule.

| Negative | What breaks |
|---|---|
| `l1_gross_off_by_one_cent` | The gross is one cent above net plus tax: entries do not balance. |
| `l2_account_closed_a_day_early` | A310 closes on 2026-03-30; I3 posts to it on 03-31. |
| `l3_line_on_both_sides` | The revenue line has a debit of 1 and a credit. |
| `l4_payment_currency_differs` | P3 is in USD; the cash account is in EUR. |
| `l5_invoice_posted_after_payment_on_same_day` | The invoice entry id sorts after the payment entry id on 2026-03-31: the receivable goes below zero. |
| `l6_remainder_cents_dropped` | The left cents go to nobody: P1 allocates 2999 of 3000. |
| `l6_payment_before_invoice_date` | The allocation ignores the invoice date: P1 pays I3 before it exists. |
| `l7_tax_truncated` | The tax rounds down: I1 has 199 instead of 200. |
| `l8_invoice_after_close` | I3 is dated 2026-04-01, after the period close. |
| `infeasible_overpayment` | P2 is 6000 and I4 is 5950. |
| `policy_not_a_date` | `period_close` is `31.03.2026`; step 10 stops (`child_execution`). |
| `payment_without_amount` | P1 is 0. |

## Known limits

- Every product that goes to the store needs a readback and an identifier, so step 93 exports each of them.
- The ledger has one receivable account for all customers; L5 checks that account, not the balance of each customer.
- The invoice lines and the payment lines are two products, so each line rule is a check product twice.

# e06 staffing register

Hidden from the subject. The subject gets `prompt.md` and `fixtures/` only.
The case asks for five tables with foreign keys and three rules across tables. The data is generated, except the functions.
`fixtures/functions.wgt.csv` is a weighted list without a header: `value|weight` on each line.
`fixtures_changed/functions.wgt.csv` holds other functions. The oracle runs the project with it too, so a typed list fails.

## Prompt to check

| Prompt requirement | Check |
|---|---|
| repeatable, seed `61423` | `seed_is`, `repeatable` |
| the project is ready (brief) | `build_ready` |
| 4 companies, `company_id` 1 to 4 | `exact_rows:companies` (other fields ignored) |
| company `name`, a text that is never empty | `text:companies.name` |
| 20 people, `person_id` 1 to 20, `badge` `P-007` form | `exact_rows:people` (other fields ignored) |
| `full_name`, a text that is never empty | `text:people.full_name` |
| 2 employments for each person, 40 in total | `exact_count:employments`, `per_parent_count:employments.person_id` |
| employment `person_id` is the person's whole number | `whole_number:employments.person_id` |
| `employment_id` is a different whole number | `unique:employments.employment_id`, `whole_number:employments.employment_id` |
| employment `company_id` is a company in `companies` | `row_exists_in:employments->companies` |
| `function` is drawn from `fixtures/functions.wgt.csv` | `value_in:employments.function` (the visible names), `value_in:employments.function:fixtures_changed` (the hidden names) |
| never two employments at the same company | `unique_together:employments.person_id+company_id` |
| 2 licenses for each person, 40 in total | `exact_count:licenses`, `per_parent_count:licenses.person_id` |
| license `person_id` is the person's whole number | `whole_number:licenses.person_id` |
| `license_id` is a different whole number | `unique:licenses.license_id`, `whole_number:licenses.license_id` |
| `valid_from` from 2026-01-01 to 2026-03-31, `YYYY-MM-DD` | `date_range:licenses.valid_from` |
| `expires_on` from 2026-03-01 to 2026-12-31 or null; exactly 10 nulls; null, not an empty text | `date_range:licenses.expires_on` (`missing: 10`) |
| 5 assignments for each company, 20 in total | `exact_count:assignments`, `per_parent_count:assignments.company_id` |
| `assignment_id` is a different whole number | `unique:assignments.assignment_id`, `whole_number:assignments.assignment_id` |
| an employment of the person at this company in this function | `row_exists_in:assignments->employments` (`person_id`, `company_id`, `function`) |
| `work_date` from 2026-03-01 to 2026-03-31, `YYYY-MM-DD` | `date_range:assignments.work_date` |
| a license valid on the `work_date`, both days count, no expiry is never valid | `row_exists_in:assignments->licenses` (window `valid_from`..`expires_on`) |
| at most one assignment of a person on the same `work_date` | `unique_together:assignments.person_id+work_date` |

The type of a foreign key is checked by `row_exists_in`: it compares the JSON types, so the text `"1"` is not the company 1.
`per_parent_count` compares as text, so `whole_number` on the key field closes that gap (README, "Oracle checks").

## Reference

`reference/` makes the rows with arithmetic in nested `<generate>` elements. Each person owns its licenses and employments.
The one assignment of a person sits under the first employment and copies it. So the employment rule holds by construction.
The work day is a person variable. The first license expires on that day, so the reference proves that the expiry day counts.
e06 proves that the rows obey the rules, not that the subject handled the expiry-day or null boundary: `row_exists_in` needs one matching license.
The function key reads the weighted file (`source=` on the `<key>`), with no separator attribute.
The 124 rows are in the Build row cap of 1000. The hidden set adds a capture run, not a Build. The assignment count is an expression, so Build cannot derive the row total: the reference sets `max_count` to 124.

## Equivalence classes

The `e06` variants and cheats in `test_authoring_eval.py` cover these classes:

- valid: `reference/`
- boundary: the work date is the expiry day (max, `reference/`), the first valid day (min, passes), max + 1, min - 1
- missing: no expiry date counted as valid; an empty text or no field for a missing date
- count of nulls: 9, 11
- count per parent: employments, licenses, assignments, companies, a person without an assignment
- duplicate: a pair in employments, a pair in assignments, ids
- invalid rule: another company, function or person
- closed set from the weighted file: a function outside the file; the visible names and weights typed into the project (fails the hidden set only); the file read through a `<variable>` (passes)
- derived field
- type: text ids and foreign keys, a date of another form, a number as a name, an empty name
- order: the people in reverse order (passes)
- seed and hash order
- cheat: random foreign keys from the right sets, with typed functions

## The weighted list

The two `value_in` checks prove the closed set of each fixture set. They do not prove the shares.
No check of the shares exists, for two reasons:

1. Every engine form that reads the file draws with the weights. `<key source>` and `<variable source>` sample with replacement.
   `distribution="ordered"` and `storage="data"` on a headerless `.wgt.csv` are refused, and `<generate source>` refuses it too.
   So a project that ignores the weights must type the names, and the hidden set fails it.
2. A frequency check is weak. "The name of weight 80 is the most frequent of the 40" is stable: an honest draw misses it with a
   probability of 8e-7. But a uniform draw passes it 30 % of the time, and a typed list with the right weights passes it always.
   On the hidden set (50/30/15/5) the reference itself draws DRIVER 18 times and WELDER 14 times, so such a check fails a valid project.

Engine facts from probes: a weight of 0 is never drawn; a duplicate value adds its weights; an empty weight on a later line stops the run with a `ValueError`.
A first line whose weight is not a number is read as a header and skipped.

`test_every_check_of_the_complex_cases_fails_in_some_variant` proves that each check fails in at least one variant or cheat.
The synthetic tests of `unique_together`, `row_exists_in` and `date_range` cover null, empty, absent, non-ISO and calendar-invalid dates.

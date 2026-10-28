# S12 Personnel and approvals

This project staffs every seat of every approval version. Each seat gets one person. Six rules (R1 to R6) decide who can take a seat.
It is the synthetic stand-in of `docs/evaluations/complex-authoring-reference.md`. All names and data are invented.
`scenario.json` lists what the project proves, the expected row counts and the negative variants.

## Process

`datamimic.xml` loads the library and runs the steps in this order:

```text
data/entity/*.json      ──► 10 prepare ──► 20 suitability ──► 30 assign ──► 90 validate output ──► 91 export ──► CSV
conf/policy.properties      policy         R1 R2 R3           R4 R5 R6      seat_check             11 tables
                            positions      (Python)           (Python)      plan_check             JSON: policy,
                            R4 maximum                                                             assignment
                                │                │                │               │                    │
                                └── memstore ────┴── memstore ────┴── memstore ───┴──── memstore ──────┘
acceptance/build.json checks the input, the plan, the trace and the 11 target tables (Build only).
```

| Step | File | Purpose |
|---|---|---|
| 10 prepare | `model/10_prepare.xml` | Types the parameters of `conf/policy.properties` once into the `policy` product. Resolves each demanded position to its approval, its company (the approval's addressee) and its date. An `<assert>` stops the run when a demand is not 1 to `max_seats` seats. |
| 20 suitability | `model/20_suitability.xml` | Calls `suitable_people` once per position: R1 to R3 for every person, the exclusions counted by rule and the near misses. |
| 30 assign | `model/30_assign.xml` | Calls `assign_seats` once: one search fills every seat under R4 to R6. It writes the plan and the counters (`assignment`) to the memstore, and the trace to JSON (see "Known limits"). It gives no plan unless every seat is filled. |
| 90 validate output | `delivery/90_validate_output.xml` | Checks the plan without the search and without step 20. `seat_check` tests R1 to R3 for each seat in XML from the raw rows and the step-10 positions. `plan_check` tests R4 to R6 for each position in XML from the plan. |
| 91 export | `delivery/91_export.xml` | Writes the 11 target tables to CSV, and `policy` and `assignment` to JSON. Staffing, `export_policy` and `export_assignment` read the memstore. |

Input validation and cleanup have no step file (see "Known limits").

## Target tables

The project delivers 11 tables with 27 columns and 540 rows. `PK` is the key that Build checks as unique. `FK` names the parent that Build checks. `acceptance/build.json` pins each row count.

| Table | Rows | Columns |
|---|---|---|
| `companies` | 10 | `company_id` PK, `company_name` |
| `people` | 100 | `person_id` PK, `full_name` |
| `functions` | 4 | `function_id` PK, `function_name` |
| `employments` | 105 | `person_id` FK people, `company_id` FK companies, `function_id` FK functions |
| `licenses` | 2 | `license_type` PK |
| `person_licenses` | 102 | `person_id` FK people, `license_type` FK licenses, `status` (`active` or `inactive`), `expires_on` (ISO date or empty) |
| `qualifications` | 4 | `qualification_id` PK, `qualification_name` |
| `person_qualifications` | 98 | `person_id` FK people, `qualification_id` FK qualifications |
| `approvals` | 11 | `approval_id` PK, `company_id` FK companies (the addressee) |
| `approval_versions` | 22 | `version_id` PK, `approval_id` FK approvals, `valid_on` (ISO date) |
| `staffing` | 82 | `seat_id` PK, `version_id` FK approval_versions, `function_id` FK functions, `person_id` FK people |

## Output

- `datamimic run datamimic.xml` writes to `output/<run-id>/`: one CSV file for each table. The delimiter is `|`. An empty field is a missing value.
- `policy.json`: one object with the typed rule parameters.
- `assignment.json`: one object with `assignment_id` (always 1), `outcome`, `nodes` (tries), `backtracks`, `unfilled_by` and `skipped_by`.
- `trace.json`: one row for each rejection of the search: `position_id`, `seat_id`, `person_id`, `full_name`, `action`, `rule`, `reason`. The actions are `skip`, `dead_end`, `undo` and `short`. The plan holds the choices.
- `seat_check.json`: one row for each seat with `r1_employed`, `r2_licensed` and `r3_qualified`.
- `plan_check.json`: one row for each of the 60 positions with `eligible`, `excluded_by`, `near_misses` and the R4 to R6 checks.
- No step draws a random value. The seed `rngSeed="12"` lets Build replay the run and compare the rows.

## Files

| File | Owner of | Read by |
|---|---|---|
| `data/entity/companies.json`, `functions.json`, `licenses.json`, `qualifications.json` | master data | step 91 |
| `data/entity/people.json` | the people and their names | steps 20, 30 (names in the trace), 91 |
| `data/entity/employments.json` | which person works for which company in which function | steps 20, 90, 91 |
| `data/entity/person_licenses.json` | license type, status and expiry of each person | steps 20, 90, 91 |
| `data/entity/person_qualifications.json` | qualifications of each person | steps 20, 90, 91 |
| `data/entity/approvals.json`, `approval_versions.json` | the approval's addressee company, the version's date | steps 10, 91 |
| `data/entity/demand.json` | seats per version and function (the positions) | step 10 |
| `conf/policy.properties` | all rule parameters, as text | step 10 (the `policy` product, read by steps 10 to 91) |
| `lib/staffing.scr.py` | `read_policy`, `suitable_people`, `assign_seats` | steps 10 to 30 |
| `acceptance/build.json` | the expectations that Build proves | Build |

The library reads no file. Step 10 types each policy parameter once; `read_policy` makes the typed `Policy` from the `policy` row.

## Rules

| Rule | Meaning | Decided in | Checked again in | Parameter in `conf/policy.properties` |
|---|---|---|---|---|
| R1 | The person has an employment at the position's company in the position's function. Its three parts are `R1_person`, `R1_company` and `R1_function`. | `_employment` | `r1_employed` | none |
| R2 | The person has an active base license, valid on the version's date. The expiry day is valid. A missing expiry is not valid. | `_base_license` | `r2_licensed` | `base_license`, `active_status` |
| R3 | The person has the qualification of the function. | `_qualification` | `r3_qualified` | `required_qualification_<function>` |
| R4 | Demand is 1 to `max_seats` seats. Different people take the seats of one position (a version and a function). | `<assert>` in step 10; `_conflict` | `distinct_people` | `max_seats` |
| R5 | A person of an exclusive approval takes no seat of another approval. Versions of one approval share people. | `_conflict` | `approval_exclusive` | `exclusive_approvals` (comma-separated ids; spaces and empty items do not count) |
| R6 | A person takes seats of one company only. Approvals of one company share people. | `_conflict` | `company_exclusive` | none |
| budget | The search stops after `search_budget` tries and reports `budget_exhausted`, not `infeasible`. | `assign_seats` | Build: `outcome != 'budget_exhausted'` | `search_budget` |

"Decided in" is a function in `lib/staffing.scr.py` or an element in `model/`. "Checked again in" is a key of step 90; Build requires it to be true for every row. "Build:" marks a Build condition on `assignment`, not a key of step 90.
When a seat stays empty, `unfilled_by.<rule> == 0` names the rule that blocked it.

## Decision evidence

- `unfilled_by` is zero when the plan is complete. Otherwise it counts the causes by rule:
  - a position with fewer eligible people than seats: one R4 count when some people are eligible, and one count for each near miss. People of other companies (`R1_company`) count only when no closer cause exists.
  - a search that finds no plan: each dead end, by the rule that took the free people of a later position.
- `skipped_by` counts, by rule, the people that the search skipped because of R4, R5 or R6.
- A near miss is a person that fails exactly one rule. A person that fails two or more rules is counted in `excluded_by`, not named.

## Control cases

Build pins each control case, so it cannot vanish when the data changes.

| Case | Data | Build expectation |
|---|---|---|
| Expiry day is valid | Person 47 is the only inspector for `A07-V1`. The license expires on 2026-03-01, the version date. | `seat_id != 'A07-V1-INS-1' or person_id == 47` |
| Versions share their approval | `A01` (exclusive) keeps person 4 for both versions. | `seat_id not in ('A01-V1-OPR-1', 'A01-V2-OPR-1') or person_id == 4` |
| Backtracking | `A03-V1-PLN` first takes person 20. Then `A05-V1-PLN` has too few people (R6). The search undoes it and takes person 94. | `outcome != 'complete' or backtracks >= 1`; the trace count 40, which holds exactly one `dead_end` row; that row is person 20 (R6); `seat_id != 'A03-V1-PLN-1' or person_id == 94` |
| R5 is used | The search skips people because of R5. | `outcome != 'complete' or skipped_by.R5 >= 1` |
| Approvals of one company share people | `A03` and `A04` (company C02) both use persons 12 and 13. | the staffing count (C02 has two eligible operators for eight seats) |
| Near misses | 1 (no expiry date), 11 (no base license), 22 (expired), 32 (inactive), 14 and 62 (no qualification). | visible in `plan_check.json`, not pinned |

## Negative variants

Each negative in `scenario.json` patches one text in one file of a copy of the project. Build must reject it with the named rule.

- The data variants change one row of one data file. Most of them change a fact of person 47, the only inspector for `A07-V1`.
- A data variant without a plan fails its named rule and also four consequences: `outcome != 'infeasible'` (or `'budget_exhausted'`), `filled == seats`, the staffing count 82 and the trace count 40.
- `r5_exclusive_approval` and `r6_cross_company` also fail the `dead_end` pin of person 20, because their search records other dead ends.
- `r4_above_maximum` stops the run in step 10. Build reports `assert_failed` with the message of the `<assert>`, and `not_executed` for the checks it could not evaluate. Build keeps the products that complete before a failed assert. Only `policy` completes before `positions`, so Build evaluates only the `policy` identifier role. The harness also runs the variant and checks the message.
- The `search_ignores_*` and `suitability_*` variants patch `lib/staffing.scr.py`. `plan_other_company` gives seat `A01-V1-INS-1` (C01) to person 15 of C02: `r1_employed` fails by its company part, and R5 and R6 as consequences. Step 90 must reject each one by the named check. The pinned control cases and the trace count can fail too, because the plan changes.
- `search_omits_dead_end_trace` deletes the `dead_end` rows from the trace. Only the trace count 40 rejects it, so the count makes the `dead_end` pin real.

The outcomes of the reference brief map to these cases:

| Outcome | Where |
|---|---|
| Backtracking | Base case: person 20 is undone in `A03-V1-PLN`, person 94 takes the seat. |
| Infeasible | `r5_exclusive_approval` and `r6_cross_company`: the search proves below the budget that no plan exists. Only search dead ends count R5 and R6 in `unfilled_by`, and an exhausted budget sets every count to 0. So `unfilled_by.R5` or `unfilled_by.R6` above 0 proves a finished search. |
| Exhausted budget | `budget_exhausted`: it reports `budget_exhausted`, never `infeasible`. |
| Expiry date is valid | Base case (person 47, pinned); `r2_expired` moves the expiry one day earlier. |
| Missing expiry is not valid | `r2_no_expiry`; `suitability_counts_missing_expiry_as_valid` breaks the rule in step 20 and step 90 rejects it. |
| Replay | The runner runs the project twice and compares the rows; Build replays the seeded model. |

## Change a rule

1. Change the parameter in `conf/policy.properties`, or a fact in a file in `data/entity/`.
2. Run `datamimic authoring build tests_ce/scenarios/s12_personnel_approvals`.
3. Read the `expected` field of each diagnostic. It names the rule.
4. Read the `trace` evidence. It names the person, the rule and the reason.

## Known limits

Product limits. Issue #420 tracks them.

- `delivery/` holds the output check and the CSV export; there is no cleanup step. Build refuses the SQL that creates a table (`unsupported_bounded_operation`), and an SQLite insert does not create its table. So the project writes CSV files, and a new run writes new files. There is no transaction boundary: each table is written on its own. The R4 assert stops the run before any CSV; an infeasible run exits 0 and writes the master tables without `staffing.csv`.
- Only the R4 maximum stops the run. The plan checks are row conditions, which only Build checks: a search with a defect still delivers a plan that breaks a rule, and the run ends with exit 0. When the plan is not complete, the run writes the master data tables and no `staffing.csv`. A failed `<assert>` stops Build at the same point as the run: Build keeps the products made before it and lists the checks it could not evaluate. An `<assert>` in step 90 can also make the plan checks stop `datamimic run`, but it sees only its own row, and it stops the run before step 91 exports.
- The export keys list the 27 columns, but they do not filter: a source field outside the list reaches the CSV. Build has no exact field-set expectation, and an export without `source=` needs a literal count that silently truncates a longer file.
- Build caps the bounded capture at 1000 rows in total. The base case uses 928. So the trace leaves out the `try` decisions, and a search mutant that skips many people can exceed the cap. `search_ignores_suitability` makes 109 trace rows and uses 997.
- A Python error in a script loses its text: a policy count that is not a whole number or a missing parameter is rejected as `child_execution` without the `ValueError` or `NameError` text. A normal run names it.
- Build reads the fields of a product from its keys. A key such as `seat_id` on `seat_check` only copies a source field, but Build needs it for the product roles.
- Steps share data only through the memstore. Build refuses `<include>` inside `<generate>`, and it accepts only a `<generate>` as a memstore reader with a declared role. So `plan_check` reads the step 20 rows.

Project limits.

- Step 30 writes `trace` to JSON from `model/`. This breaks separation rule 3 of the project standard. A memstore copy and an `export_trace` count the trace twice against the Build limit of 1000 rows, and `search_ignores_suitability` then exceeds it. `assignment` goes through the memstore: Build needs a producer identifier for the readback, so `assignment.json` has `assignment_id` (#411).
- The data files are JSON in `data/entity/`, not `.ent.csv`. A CSV cell is text, so the numbers and the `null` expiry need one typed memstore copy of each table. Each copy counts against the Build limit of 1000 rows: one typed copy of `people` makes 1028 rows. For the same reason steps 90 and 91 read the data files directly, not the memstore (rule 3).
- Input validation runs in Build only, except the R4 maximum.
- Rows stored in a `<variable>` list lose dot access (#441), so the R5 and R6 keys of `plan_check` read `other['company_id']`.
- Step 20 keeps R1 to R3 in Python: the search reads the near misses, and each one names the failed part of R1 or the R2 reason. In XML that is one long conditional per rule. Step 90 states R1 to R3 a second time in XML, for each seat.
- R3 cannot say "active": `person_qualifications` has no status column. A qualification row counts as active.
- A person that fails two or more rules is counted, not named.
- Step 10 types the policy parameters only; the data files get no type check. A wrong value fails a rule or stops the run.
- The infeasible cases need 1 to 7 tries; forward checking finds them early. No case needs a long search to prove infeasibility.

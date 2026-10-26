# S12 Personnel and approvals

This project staffs every seat of every approval version. Each seat gets one person. Six rules (R1 to R6) decide who can take a seat.
It is the synthetic stand-in of `docs/evaluations/complex-authoring-reference.md`. All names and data are invented.

## Process

`datamimic.xml` loads the library and runs the steps in this order:

```text
data/*.json ──► 1 prepare ──► 2 suitability ──► 3 assign ──► 4 validate output ──► 5 export ──► CSV
   (owners)     positions      R1 R2 R3          R4 R5 R6      plan_check            11 tables
                    │              │                │               │
                    └── memstore ──┴── memstore ────┴── memstore ───┘
acceptance/build.json checks the input, the plan and the 11 target tables (Build only).
```

| Step | File | Purpose |
|---|---|---|
| 1 prepare | `model/1_prepare.xml` | Resolves each demanded position to its approval, its company (the approval's addressee) and its date. |
| 2 suitability | `model/2_suitability.xml` | Decides R1 to R3 for every person and position. Counts the exclusions by rule and names the near misses. |
| 3 assign | `model/3_assign.xml` | One search fills every seat under R4 to R6. It records each decision. It gives no plan unless every seat is filled. |
| 4 validate output | `model/4_validate_output.xml` | Checks the plan of each position without the search. |
| 5 export | `model/5_export.xml` | Writes the 11 target tables to CSV. Staffing reads the checked plan from the memstore. |

Input validation and cleanup have no model file. Build checks the input in `acceptance/build.json` (see "Known limits").
Each step reads `data/policy.json` through `read_policy`, which checks the type of each parameter.

## Target tables

The project delivers 11 tables with 27 columns and 540 rows. `PK` is the key that Build checks as unique. `FK` names the parent that Build checks.

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

The row counts are the project's contract. `acceptance/build.json` pins each count, so a data change that adds or removes rows fails Build.

## Output

- `datamimic run datamimic.xml` writes to `output/<run-id>/`. One CSV file for each table, for example `output/<run-id>/staffing.csv`.
- A CSV file has a header row. The delimiter is `|`. An empty field is a missing value (`expires_on`).
- `assignment.json` is a list with one object: `outcome`, `nodes` (tries), `backtracks`, `unfilled_by`, `skipped_by` and `decisions`.
- `plan_check.json` is a list with one object for each of the 60 positions: the position, `eligible`, `excluded_by`, `near_misses` and the checks of step 4.
- The seed is `rngSeed="12"` in `datamimic.xml`. No step draws a random value, so every seed gives the same files (seeds 12 and 99 give identical files). The seed makes Build replay the run and compare the rows.

## Files

| File | Owner of | Read by |
|---|---|---|
| `data/companies.json`, `people.json`, `functions.json`, `licenses.json`, `qualifications.json` | master data | step 2 (people), step 5 |
| `data/employments.json` | which person works for which company in which function | step 2, step 5 |
| `data/person_licenses.json` | license type, status and expiry of each person | step 2, step 5 |
| `data/person_qualifications.json` | qualifications of each person | step 2, step 5 |
| `data/approvals.json`, `approval_versions.json` | the approval's addressee company, the version's date | step 1, step 5 |
| `data/demand.json` | seats per version and function (the positions) | step 1 |
| `data/policy.json` | all rule parameters | steps 1 to 3 |
| `lib/staffing.scr.py` | `read_policy` and the three functions below | steps 1 to 4 |
| `acceptance/build.json` | the expectations that Build proves | Build |
| `scenario.json` | expected rows and the negative variants | `tests_ce/scenarios/test_scenarios.py` |

The library has three functions that the steps call. None of them reads a file.

- `suitable_people` gets one position and the person rows. It returns the eligible people, the exclusions counted by rule and the near misses (people that fail one rule).
- `assign_seats` gets all positions with their eligible people and the policy. It returns the outcome, the plan and the decisions.
- `check_position` gets one position and the plan. It returns the R4 to R6 checks of step 4. Step 4 checks R1 to R3 for each seat in XML (`seat_check`), from the raw rows.

## Rules

| Rule | Meaning | Decided in | Parameter in `data/policy.json` | Build expectation |
|---|---|---|---|---|
| R1 | The person has an employment at the position's company in the position's function. It has three parts: `R1_person`, `R1_company`, `R1_function`. | `_employment` | none | `unfilled_by.R1_person == 0`, `unfilled_by.R1_company == 0`, `unfilled_by.R1_function == 0`, `r1_employed` (step 4) |
| R2 | The person has an active base license. It is valid on the version's date; the expiry day is valid; no expiry date is not valid. | `_base_license` | `base_license`, `active_status` | `unfilled_by.R2 == 0`, `r2_licensed` (step 4) |
| R3 | The person has the qualification of the function. | `_qualification` | `required_qualification` | `unfilled_by.R3 == 0`, `r3_qualified` (step 4) |
| R4 | Demand is 1 to `max_seats` seats. Different people take the seats of one position. A position is a version and a function. | `<assert>` in step 1 (the run stops), `_conflict` | `max_seats` | `child_execution` at `model/1_prepare.xml/assert`, `unfilled_by.R4 == 0`, `distinct_people` |
| R5 | A person of an exclusive approval takes no seat of another approval. Versions of one approval share people. | `_conflict` | `exclusive_approvals` | `unfilled_by.R5 == 0`, `skipped_by.R5 >= 1`, `approval_exclusive` |
| R6 | A person takes seats of one company only. Approvals of one company share people. | `_conflict` | none | `unfilled_by.R6 == 0`, `company_exclusive` |
| budget | The search stops after `search_budget` tries. It then reports `budget_exhausted`, not `infeasible`. | `assign_seats` | `search_budget` | `outcome != 'budget_exhausted'` |

All rule functions are in `lib/staffing.scr.py`. All expectations are in `acceptance/build.json`.
`skipped_by.R5 >= 1` proves that the base case uses R5: with an empty `exclusive_approvals`, Build rejects the project.

## Decision evidence

- `unfilled_by` is zero for every rule when the plan is complete. When it is not complete, it counts by rule:
  - for a position with fewer eligible people than seats: each near-miss person (one count for each person), and one R4 count when some people are eligible;
  - for a search that finds no plan: each dead end, by the rule that took the free people of a later position.
- So a large count does not mean a large cause. `R1_company` is usually large, because qualified people of other companies fail only R1. The smallest count that is not zero usually names the cause.
- `skipped_by` counts, by rule, the people that the search skipped because of R4, R5 or R6.
- `decisions` names the position, the seat, the person, the action, the rule and the reason. Actions: `try`, `skip`, `dead_end`, `undo`, `short`.
- A near miss is a person that fails exactly one rule. A person that fails two or more rules is counted in `excluded_by`, not named.

## Control cases

Build pins each control case, so it cannot vanish when the data changes.

| Case | Data | Build expectation |
|---|---|---|
| Expiry day is valid | Person 47 is the only inspector for `A07-V1`. The license expires on 2026-03-01, the version date. | `seat_id != 'A07-V1-INS-1' or person_id == 47` |
| Versions share their approval | `A01` (exclusive) keeps person 4 for both versions. | `seat_id not in ('A01-V1-OPR-1', 'A01-V2-OPR-1') or person_id == 4` |
| Backtracking | `A03-V1-PLN` first takes person 20. Then `A05-V1-PLN` has too few people (R6). The search undoes it and takes person 94. | `backtracks >= 1`, `seat_id != 'A03-V1-PLN-1' or person_id == 94` |
| R5 is used | The search skips people because of R5. | `skipped_by.R5 >= 1` |
| Approvals of one company share people | `A03` and `A04` (company C02) both use persons 12 and 13. | the staffing count (C02 has two eligible operators for eight seats) |
| Near misses | 1 (no expiry date), 11 (no base license), 22 (expired), 32 (inactive), 14 and 62 (no qualification). | visible in `plan_check.json`, not pinned |

## Negative variants

Each variant in `scenario.json` patches one row of one data file in a copy of the project. Build must reject the variant.

| Variant | Changed fact | Build reports (`expected`) |
|---|---|---|
| `r1_person` | The employment of person 47 names person 100. | `unfilled_by.R1_person == 0` |
| `r1_company` | Person 47 works for company C10. | `unfilled_by.R1_company == 0` |
| `r1_function` | Person 47 works as planner. | `unfilled_by.R1_function == 0` |
| `r2_missing` | The base license of person 47 is a trainee license. | `unfilled_by.R2 == 0` |
| `r2_expired` | It expires one day before the version date. | `unfilled_by.R2 == 0` |
| `r2_inactive` | It is inactive. | `unfilled_by.R2 == 0` |
| `r2_no_expiry` | It has no expiry date. | `unfilled_by.R2 == 0` |
| `r3_missing` | Person 47 has the planner qualification, not the inspector one. | `unfilled_by.R3 == 0` |
| `r4_above_maximum` | `A11-V1-OPR` asks for 4 seats. The run stops in step 1. | `child_execution` |
| `r4_same_person` | `A07-V1-INS` asks for 2 seats. Only person 47 is eligible. | `unfilled_by.R4 == 0` |
| `r5_exclusive_approval` | `A01-V1-OPR` asks for 2 seats. The search proves it infeasible. | `unfilled_by.R5 == 0` |
| `r6_cross_company` | Person 47 is also the only inspector of company C06. | `unfilled_by.R6 == 0` |
| `infeasible` | Person 94 no longer works at C02. `A03-V1-PLN` and `A05-V1-PLN` both need person 20. The search proves that no plan exists. | `outcome != 'infeasible'` |
| `budget_exhausted` | `search_budget` is 50. The base case needs 83 tries. | `outcome != 'budget_exhausted'` |

`scenario.json` names this `expected` text for each variant, so CI checks the rule and not only the code `row_condition`.
A variant that leaves a seat empty also fails other expectations, for example `outcome != 'infeasible'`, `filled == seats` and the staffing count.

The `search_ignores_*` negatives patch `lib/staffing.scr.py` and break the search four times. Step 4 must reject each one:

| Mutant | Changed lines | Build reports |
|---|---|---|
| `search_ignores_suitability` | the search also tries the near misses | `r1_employed` |
| `search_ignores_r4` | the R4 check in `_conflict` is removed | `distinct_people` |
| `search_ignores_r5` | the R5 check in `_conflict` is removed | `approval_exclusive` |
| `search_ignores_r6` | the R6 check in `_conflict` is removed | `company_exclusive` |

The six outcomes of the reference brief map to these cases:

| Outcome | Where |
|---|---|
| Backtracking | Base case: `backtracks >= 1` and person 94 in `A03-V1-PLN`. |
| Infeasible | `infeasible`; also `r5_exclusive_approval` and `r6_cross_company`, which end below the budget. |
| Exhausted budget | `budget_exhausted`; it reports `budget_exhausted`, never `infeasible`. |
| Expiry date is valid | Base case (person 47, pinned); `r2_expired` moves the expiry one day earlier. |
| Missing expiry is not valid | `r2_no_expiry`; person 1 in the base case is a near miss for this reason. |
| Replay | The runner runs the project twice and compares the rows; Build replays the seeded model (803 rows). |

## Change a rule

1. Change the parameter in `data/policy.json`, or a fact in a file in `data/`.
2. Run `datamimic authoring build tests_ce/scenarios/s12_personnel_approvals`.
3. Read the `expected` field of each diagnostic. It names the rule.
4. Read `decisions` in the `assignment` evidence. It names the person and the reason.

## Known limits

Product limits. Issue #420 tracks them.

- No `delivery/` and no cleanup step. Build refuses the SQL that creates a table (`unsupported_bounded_operation`), and an SQLite insert does not create its table. So the project writes CSV files, and a new run writes new files.
- A plain `datamimic run` does not stop on a broken plan, because Build drops the message of a failed `<assert>` (only `child_execution`). So the rules are row conditions, which only Build checks. A search with a defect still delivers a plan that breaks a rule, and the run ends with exit 0. When the plan is not complete, the run writes the master data tables and no `staffing.csv`.
- A Python error in a script loses its text: a wrong policy type is rejected as `child_execution` without the message of `read_policy`.
- `type=` on a memstore reader also names the entity that it writes. A reader that writes to the memstore again uses `sourceEntity=`.
- A generator expression in `script=` cannot see `this`. The lookups in step 1 use a dict comprehension: `{row.version_id: row for row in versions}[this.version_id]`.
- Steps share data only through the memstore. Build refuses `<include>` inside `<generate>`, and it accepts only a `<generate>` as a memstore reader.
- A JSON object in a row is a `Mapping` without `values()` or `items()`. `read_policy` copies it by key.

Project limits.

- Input validation runs in Build only.
- R1 to R3 are Python functions, because the DSL has no lookup across rows of other tables. Step 2 calls them once per position.
- R3 cannot say "active": `person_qualifications` has no status column. A qualification row counts as active.
- A person that fails two or more rules is counted, not named.
- `unfilled_by.R1_company == 0` also fails in R2, R3 and R4 variants, so `r1_company` is the weakest R1 variant.
- The exact row counts stay pinned (review finding F6). They are the contract of this project, not a rule.
- `read_policy` checks the policy types only; the data files get no type check (review finding F8). A wrong value fails a rule or stops the run.
- The infeasible cases need 1 to 7 tries; forward checking finds them early. No case needs a long search to prove infeasibility (review finding F9).

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
| 2 suitability | `model/2_suitability.xml` | Decides R1 to R3 for every person and position. Keeps the eligible people and the near misses. |
| 3 assign | `model/3_assign.xml` | One search fills every seat under R4 to R6. It records each decision. It gives no plan unless every seat is filled. |
| 4 validate output | `model/4_validate_output.xml` | Checks the plan of each position without the search. |
| 5 export | `model/5_export.xml` | Writes the 11 target tables to CSV. Staffing reads the checked plan from the memstore. |

Input validation and cleanup have no model file. Build checks the input in `acceptance/build.json` (see "Limits").

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
| `lib/staffing.scr.py` | the three typed functions below | steps 2 to 4 |
| `acceptance/build.json` | the expectations that Build proves | Build |
| `scenario.json` | expected rows and the negative variants | `tests_ce/scenarios/test_scenarios.py` |
| `test_s12_mutants.py` | the check that each search mutant in `negative/` matches the library | pytest |

The library has three public functions. None of them reads a file.

- `suitable_people` gets one position and the person rows. It returns the eligible people, the exclusions counted by rule and the near misses (people that fail one rule).
- `assign_seats` gets all positions with their eligible people and the policy. It returns the outcome, the plan and the decisions.
- `check_position` gets one position and the plan. It returns the checks of step 4.

## Rules

| Rule | Meaning | Decided in | Parameter in `data/policy.json` | Build expectation |
|---|---|---|---|---|
| R1 | The person has an employment at the position's company in the position's function. It has three parts: `R1_person`, `R1_company`, `R1_function`. | `_employment` | none | `unfilled_by.R1_person == 0`, `unfilled_by.R1_company == 0`, `unfilled_by.R1_function == 0`, `all_eligible` |
| R2 | The person has an active base license. It is valid on the version's date; the expiry day is valid; no expiry date is not valid. | `_base_license` | `base_license`, `active_status` | `unfilled_by.R2 == 0`, `all_eligible` |
| R3 | The person has the qualification of the function. | `_qualification` | `required_qualification` | `unfilled_by.R3 == 0`, `all_eligible` |
| R4 | Demand is 1 to `max_seats` seats. Different people take the seats of one position. | `positions` (step 1), `_conflict` | `max_seats` | `seats >= 1 and seats <= max_seats`, `unfilled_by.R4 == 0`, `distinct_people` |
| R5 | A person of an exclusive approval takes no seat of another approval. Versions of one approval share people. | `_conflict` | `exclusive_approvals` | `unfilled_by.R5 == 0`, `approval_exclusive` |
| R6 | A person takes seats of one company only. Approvals of one company share people. | `_conflict` | none | `unfilled_by.R6 == 0`, `company_exclusive` |
| budget | The search stops after `search_budget` tries. It then reports `budget_exhausted`, not `infeasible`. | `assign_seats` | `search_budget` | `outcome != 'budget_exhausted'` |

All rule functions are in `lib/staffing.scr.py`. All expectations are in `acceptance/build.json`.

## Decision evidence

- `assignment.json` has the outcome, the number of tries (`nodes`), the backtracks and `unfilled_by` (seats left empty, counted by rule).
- Its `decisions` list names the position, the seat, the person, the action, the rule and the reason. Actions: `try`, `skip`, `dead_end`, `undo`, `short`.
- `plan_check.json` has, for each position, the eligible people, `excluded_by` (people excluded, counted by rule), the near misses with rule and reason, and the checks of step 4.
- A near miss is a person that fails exactly one rule. A person that fails two or more rules is counted, not named.

## Control cases in the data

| Case | Data |
|---|---|
| Expiry day is valid | Person 47 is the only inspector for `A07-V1`. The license expires on 2026-03-01, the version date. |
| Backtracking | `A03-V1-PLN` first takes person 20. Then `A05-V1-PLN` has too few people (R6). The search undoes it and takes person 94. |
| Versions share their approval | `A01` (exclusive) keeps person 4 for both versions. |
| Approvals of one company share people | `A03` and `A04` (company C02) both use persons 12 and 13. |
| Near misses | 1 (no expiry date), 11 (no base license), 22 (expired), 32 (inactive), 14 and 62 (no qualification). |

## Negative variants

Each directory in `negative/` holds one file that differs from the project. The runner copies it over the project. Build must reject the variant.

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
| `r4_above_maximum` | `A11-V1-OPR` asks for 4 seats. | `seats >= 1 and seats <= max_seats` |
| `r4_same_person` | `A07-V1-INS` asks for 2 seats. Only person 47 is eligible. | `unfilled_by.R4 == 0` |
| `r5_exclusive_approval` | `A01-V1-OPR` asks for 2 seats. The search proves it infeasible. | `unfilled_by.R5 == 0` |
| `r6_cross_company` | Person 47 is also the only inspector of company C06. | `unfilled_by.R6 == 0` |
| `infeasible` | Person 94 no longer works at C02. `A03-V1-PLN` and `A05-V1-PLN` both need person 20. The search proves that no plan exists. | `outcome != 'infeasible'` |
| `budget_exhausted` | `search_budget` is 50. The base case needs 83 tries. | `outcome != 'budget_exhausted'` |
| `search_ignores_suitability` | The search also tries the near misses. | `all_eligible` |
| `search_ignores_r4` | The search skips the R4 check. | `distinct_people` |
| `search_ignores_r5` | The search skips the R5 check. | `approval_exclusive` |
| `search_ignores_r6` | The search skips the R6 check. | `company_exclusive` |

`scenario.json` names this `expected` text for each variant, so CI checks the rule and not only the code `row_condition`.
An infeasible variant also fails `outcome != 'infeasible'`, `filled == seats` and the staffing count.
`unfilled_by.R1_company` is not zero in every variant that leaves a seat with nobody, because qualified people of other companies fail only R1. So `r1_company` is the only R1 variant whose text other variants also show.

Each `search_ignores_*` variant holds a copy of `lib/staffing.scr.py` with one check changed.
`test_s12_mutants.py` fails when a copy differs from the library in more than that change. When you change the library, copy the change to the four mutants.

The six outcomes of the reference brief map to these cases:

| Outcome | Where |
|---|---|
| Backtracking | Base case: `backtracks >= 1` (`A03-V1-PLN`). |
| Infeasible | `infeasible`; also `r5_exclusive_approval` and `r6_cross_company`, which end below the budget. |
| Exhausted budget | `budget_exhausted`; it reports `budget_exhausted`, never `infeasible`. |
| Expiry date is valid | Base case (person 47); `r2_expired` moves the expiry one day earlier. |
| Missing expiry is not valid | `r2_no_expiry`; person 1 in the base case is a near miss for this reason. |
| Replay | The runner runs the project twice and compares the rows; Build replays the seeded model (803 rows). |

## Change a rule

1. Change the parameter in `data/policy.json`, or a fact in a file in `data/`.
2. Run `datamimic authoring build tests_ce/scenarios/s12_personnel_approvals`.
3. Read the `expected` field of each diagnostic. It names the rule.
4. Read `decisions` in the `assignment` evidence. It names the person and the reason.

## Known limits of this project

These limits come from the product. Issue #420 tracks them.

- No `delivery/` and no cleanup step. Build refuses the SQL that creates a table (`unsupported_bounded_operation`), and an SQLite insert does not create its table. So the project writes CSV files.
- A plain `datamimic run` does not stop on a broken plan. Build drops the message of a failed `<assert>` and reports only `child_execution`. So the rules are row conditions, which only Build checks.
- `type=` on a memstore reader also names the entity that it writes. A reader that writes to the memstore again uses `sourceEntity=`.
- A generator expression in `script=` cannot see `this`. The lookups in step 1 use a dict comprehension: `{row.version_id: row for row in versions}[this.version_id]`.
- Steps share data only through the memstore. Build refuses `<include>` inside `<generate>`, and it accepts only a `<generate>` as a memstore reader.

## Other limits

- Cleanup: the project writes CSV files. A new run writes new files, so no old rows remain. A database target needs a `<database>` in `delivery/` and `target="<id>.clear"` statements. Build refuses the SQL that creates the tables, so this project does not use a database.
- Input validation runs in Build only. A plain `datamimic run` does not stop on bad input or a broken plan. When the plan is not complete, the run ends with `status=ok`, writes the master data tables and writes no `staffing.csv`.
- R1 to R3 are Python functions, because the DSL has no lookup across rows of other tables. Step 2 calls them once per position.

# S13 shift roster

This project makes the roster of two hospital wards for one week. Each shift of each ward gets the people it needs.
The people must hold a valid certification, get enough rest, and stay within their contract hours.
All names and data are synthetic.

## Process

The entry `datamimic.xml` runs the steps in this order.

```text
data/*.csv ──> 1 prepare ──> (validate input) ──> 2 suitability ──> 3 assign ──> 4 validate output ──> (cleanup) ──> 5 export
               typed tables   build.json            RS1, RS6          search        RS1..RS6 again                     CSV files
               slots          expectations          candidates        RS2..RS5      check products
```

| Step | File | Purpose |
|---|---|---|
| 1 prepare | `model/1_prepare.xml` | Read each data file, give each column its type, and make one slot for each demand row and plan day. |
| validate input | `acceptance/build.json` | The input expectations check the prepared tables. There is no step file. |
| 2 suitability | `model/2_suitability.xml` | For each person and plan day, decide which shift types the person may work, and why not. |
| 3 assign | `model/3_assign.xml` | Search for one complete roster and keep the evidence of each decision. |
| 4 validate output | `model/4_validate_output.xml` | Measure the complete roster against every rule again, from the data. Build compares the measured values. |
| cleanup | none | See [Cleanup](#cleanup). |
| 5 export | `model/5_export.xml` | Read each product back from the store and write it to a CSV file. |

Every step hands its products to the next step through the memory store `mem`.

The output checks are a gate in Build only. `datamimic authoring build` rejects the project when a check fails, and the
proof names the digest of each file it read. A plain `datamimic run` does not read `acceptance/build.json`: it exports
the roster that the search returns, also when that roster breaks a rule. Run only a project whose files Build proved.

## Files

| File | Owner of |
|---|---|
| `data/staff.csv` | The people and their contract. |
| `data/contracts.csv` | The maximum weekly hours of each contract. |
| `data/certifications.csv` | The certification kinds. |
| `data/staff_certifications.csv` | Who holds which certification, from which day, until which day. An empty `expires_on` is a missing expiry date. |
| `data/wards.csv` | The wards. |
| `data/shift_types.csv` | The start hour, the length and the required certification of each shift type. |
| `data/demand.csv` | For each ward and shift type: the minimum and maximum staff, the lead certification and the minimum number of lead holders. |
| `data/leave.csv` | Leave periods and their status. Only `approved` leave blocks a person. |
| `data/calendar.csv` | The plan days. This file is the clock of the plan: nothing reads the system time. |
| `data/policy.properties` | The rule parameters: `min_rest_hours` and `search_budget`. |
| `lib/roster_rules.scr.py` | The per-row rule evidence: one named function for each rule check (see [Python](#python)). |
| `lib/roster_search.scr.py` | The global search `plan_roster`. |
| `acceptance/build.json` | The roles, the input expectations, the rule expectations and the caller's edge controls. |
| `scenario.json` | What the corpus runner checks: the row counts and the negatives. |

## Rules

| Rule | Decided in | Checked in the output | Parameter from |
|---|---|---|---|
| RS1 certification valid on the shift date | `certificate_status` (`lib/roster_rules.scr.py:27`), called by `model/2_suitability.xml:19` | `cert_status == 'valid'` on `entry_checks` (`acceptance/build.json:59`) | `data/shift_types.csv` (`required_cert`), `data/staff_certifications.csv` |
| RS2 rest between two shifts, no overlap | `blocker` in `plan_roster` (`lib/roster_search.scr.py:59`) | `entry_checks.rest_hours >= min_rest_hours` (`acceptance/build.json:60`) | `data/policy.properties` (`min_rest_hours`) |
| RS3 weekly hours within the contract | `blocker` in `plan_roster` | `hours_checks.busiest_week_hours <= contract_hours` (`acceptance/build.json:61`) | `data/contracts.csv` |
| RS4 minimum and maximum staff, minimum lead holders | `solve` and `shortage` in `plan_roster` | `coverage_checks` (`acceptance/build.json:62`, `:63`) | `data/demand.csv` |
| RS5 one ward per day | `blocker` in `plan_roster` | `wards_that_day == 1` on `entry_checks` (`acceptance/build.json:64`) | the rule itself |
| RS6 never rostered on approved leave | `on_approved_leave` (`lib/roster_rules.scr.py:45`), called by `model/2_suitability.xml:15` | `not on_leave` on `entry_checks` (`acceptance/build.json:65`) | `data/leave.csv` |

The output checks read the roster and the data again. They do not read the suitability decisions or the search evidence.
A rule that the search breaks is therefore caught, also when the search itself has a defect.
RS1 and RS6 use one function in suitability and in the output check. A defect in that function is caught only by the
caller's edge controls below, not by the output check.

RS1 has two edge cases:

- The expiry date is inclusive. S07 holds ALS until 2026-03-04, so S07 may work the night shift on that day, but not on 2026-03-05.
- A missing expiry date is not unlimited validity. S09 holds ALS without an expiry date, so S09 never works a night shift.

A certification is not valid before its issue date: the ALS of S06 starts on 2026-03-03.
RS6 has its own edges: the last day of a leave is a leave day (S03 on 2026-03-04, not on 2026-03-05),
and a requested leave does not block (S14 on 2026-03-05).

The caller's edge controls in `acceptance/build.json:68` to `:74` name these cases with their ids.

## Decision evidence

| Product | Content |
|---|---|
| `candidates` | One row for each person and plan day. `shifts` holds one decision for each shift type: `cert_status`, and `excluded_by` (`RS1`, `RS6` or empty). |
| `plan` | `outcome`, `search_complete`, `message`, `steps`, `backtracks` and `search_budget`. |
| `slot_decisions` | For each slot: the assigned people, and for each other suitable person the rule and the reason (`RS2`, `RS3`, `RS5`, or `RS4` when the demand is already met). |
| `entry_checks`, `hours_checks`, `coverage_checks` | The measured values that the rule expectations compare. |

## Search

`plan_roster` staffs every slot at its minimum. It is a depth-first search with backtracking.

1. Sort the slots by start time, then by ward.
2. For each slot, try the teams of suitable people in a fixed order: fewest hours so far first, then by id.
3. After each choice, check that every later slot can still get its minimum staff and lead holders. If not, undo the choice (a backtrack).
4. Count each tried team as one step. Stop at `search_budget` steps.

The order is fixed, so the same inputs give the same plan. The first descent is the greedy pass.

**Backtracking case.** On Monday 2026-03-02 only S01 holds ICU and ALS: S03 is on leave and the ALS of S06 starts on 2026-03-03.
The greedy pass gives the W1 night shift to S01, who comes first. Then the W2 night shift has no ICU lead.
The search undoes this choice and gives W1 to S02. The caller control `backtracks >= 1` (`acceptance/build.json:75`) proves this.

**Three outcomes.** They have different values and messages.

| `outcome` | `search_complete` | Meaning |
|---|---|---|
| `solved` | true | Every slot is staffed. |
| `infeasible` | true | No roster exists. The message names the slot and the shortage, or says that every team failed. |
| `budget_exhausted` | false | The search stopped at `search_budget` steps. This is not a proof that no roster exists. |

## Replay

`rngSeed` is set and the search uses no random value. The plan days come from `data/calendar.csv`.
The same model, data, seed and calendar give the same roster. Build replays the seeded run and compares every row.

## Python

A lookup by one key works natively with a dict index, for example
`{row.contract_id: row.max_weekly_hours for row in contracts}[contract_id]`. The project uses this form.
A lookup or a sum over another table that filters by a field of the current record does not work in `script=`,
for example "the holdings of this person". A comprehension does not see the fields of the current record.
For this reason, each of these rule checks is one small named function in `lib/roster_rules.scr.py`.
Suitability and the output checks call the same function, so each rule has one definition.

A library shares its names with the scripts. The libraries import the module `datetime`, not its classes:
the class `datetime` would hide the module `datetime` that the scripts use.

## Cleanup

There is no cleanup step. The CSV exporter writes a new output directory for each run, so no rows of an earlier run remain.
A database target needs a cleanup step that deletes the earlier rows after the output checks. A CE SQLite insert needs
an existing table, and Build refuses the SQL `execute` that creates it. For this reason this project uses CSV files.
The export is not a transaction: the files are written one after the other.

## Negatives

Each negative holds only the files that differ from the project.

| Negative | What breaks | `row_condition` that Build reports |
|---|---|---|
| `rs1_certificate_ignored` | Suitability ignores the certification. | `cert_status == 'valid'` |
| `rs1_expiry_exclusive` | The expiry date is read as exclusive. | `row_condition`, caller control for S07 on 2026-03-04 |
| `rs1_missing_expiry_unlimited` | A missing expiry date is read as valid. | `row_condition`, caller control for S09 |
| `rs1_issue_date_ignored` | The issue date is ignored: a certification is valid before it starts. | `row_condition`, caller control for S06 on 2026-03-02 |
| `rs2_rest_ignored` | The assign step gives the search 0 hours of rest. | `row_condition` on `entry_checks.rest_hours` |
| `rs3_over_contract` | One extra entry after the search: S11 works 36 h of 32 h. | `row_condition` on `hours_checks` |
| `rs4_lead_ignored` | The assign step gives the search no lead requirement. | `row_condition` on `coverage_checks.leads` |
| `rs4_over_max` | Two extra entries after the search: 3 people in a slot with a maximum of 2. | `row_condition` on `coverage_checks.staffed` |
| `rs5_second_ward` | One extra entry after the search: S07 works in W1 and W2 on one day. | `wards_that_day == 1` |
| `rs6_leave_ignored` | Suitability ignores the leave. | `not on_leave` |
| `rs6_leave_end_exclusive` | The last day of a leave is read as exclusive. | `row_condition`, caller control for S03 on 2026-03-04 |
| `infeasible_monday_lead` | S01 is on leave on Monday: no one can lead the W2 night shift. The check before the search proves it. | `outcome != 'infeasible'` |
| `infeasible_after_search` | The W1 night shift also needs an ICU lead. Each Monday night slot alone has a lead (S01), both together have not. The search tries every team. | `outcome != 'infeasible'` |
| `budget_exhausted` | `search_budget` is 50. | `search_complete == True` |

When a negative changes the suitability or the lead requirement, the search does not need its backtrack.
Then the caller control `backtracks >= 1` also fails. This is not a second broken rule.

Every rule check is a `row_condition`, so its `expected` text in `scenario.json` is the condition, which names the
rule. The plan has two checks: `outcome != 'infeasible'` fails only when no roster exists, and
`search_complete == True` fails only when the budget ran out. Together they mean `solved`, because the search has
three outcomes. The two infeasible negatives share `outcome != 'infeasible'`: they prove the same outcome on two paths,
and the `plan.message` shows which path (a slot shortage before the search, or every team failing in the search).

An overlay replaces whole files. Four negatives therefore hold a full copy of `lib/roster_rules.scr.py`
(`rs1_expiry_exclusive`, `rs1_missing_expiry_unlimited`, `rs1_issue_date_ignored`, `rs6_leave_end_exclusive`).
When you change that library, change each copy too: `diff lib/roster_rules.scr.py negative/<name>/lib/roster_rules.scr.py`
must show only the one changed line. `budget_exhausted/data/policy.properties` repeats `min_rest_hours=11` for the
same reason: an overlay cannot change one property, and without the line `min_rest_hours` is not defined.

## Known limits of this project

- The output checks are a gate in Build only. A plain `datamimic run` exports the roster without the checks, and an
  `<assert>` gate would hide its message and all evidence in Build (F13, #420).
- There is no `delivery/` folder and no cleanup step. A SQLite target needs an existing table, and Build refuses the
  SQL that creates it, so the project writes CSV files (F19, #420).
- `lib/roster_rules.scr.py` holds rule checks in Python, not only the search. A `script=` comprehension does not see
  the fields of the current record (F1, #423).
- The libraries import the module `datetime`, because a library name hides a script global of the same name (F3, #423).
- Every store read uses `sourceEntity=`, not `type=`: `type=` also sets the entity that a step writes (F4, #422).
- The `nestedKey` in suitability builds new dicts for its items and never uses `row.to_dict()`: that call returns the
  stored row, and the enrichment would change the store (F2, #421).

## Size

The ten tables (nine data tables and the roster) hold 125 rows. Build counts every captured row,
including the evidence, the checks and the export readbacks: 725 rows of the maximum of 1000.
This maximum, not the business case, sets the size of the week.

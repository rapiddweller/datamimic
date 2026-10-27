# S13 shift roster

This project makes the roster of two hospital wards for one week. Each shift of each ward gets the people it needs.
The people must hold a valid certification, get enough rest, and stay within their contract hours.
All names and data are synthetic.

## Run the tests

```bash
pytest tests_ce/scenarios -q -k s13
datamimic authoring build tests_ce/scenarios/s13_shift_roster
```

The first command Builds, runs and replays the project, and Builds each negative. The tests live in
`tests_ce/scenarios/test_scenarios.py`, so `pytest tests_ce/scenarios/s13_shift_roster` finds no tests.

## Process

The entry `datamimic.xml` runs the steps in this order. Each step is one file in `model/`.

```text
data/* ──> 1 prepare ──> 2 validate input ──> 3 suitability ──> 4 assign ──> 5 validate output ──> 6 cleanup ──> 7 export
           typed tables   leave_checks,        RS1, RS6          search       RS1..RS6 again        no-op         CSV files
           policy, slots  certification_checks candidates        RS2..RS5     check products
```

| Step | File | Purpose |
|---|---|---|
| 1 prepare | `model/1_prepare.xml` | Read each data file and the policy, give each column its type, and make one slot for each demand row and plan day. |
| 2 validate input | `model/2_validate_input.xml` | Measure the leave and certification periods. Build compares them with the input expectations. |
| 3 suitability | `model/3_suitability.xml` | For each person and plan day, decide which shift types the person may work, and why not. |
| 4 assign | `model/4_assign.xml` | Search for one complete roster and keep the evidence of each decision. |
| 5 validate output | `model/5_validate_output.xml` | Measure the complete roster against every rule again, from the data. Build compares the measured values. |
| 6 cleanup | `model/6_cleanup.xml` | Nothing to delete. See [Cleanup](#cleanup). |
| 7 export | `model/7_export.xml` | Read each product back from the store and write it to a CSV file. |

Every step hands its products to the next step through the memory store `mem`.

The checks are a gate in Build only. `datamimic authoring build` rejects the project when a check fails. A plain
`datamimic run` exports a roster that breaks a rule and ends with exit code 0. Only an `<assert>` stops a run; see
`datamimic authoring reference --topic learning --name assert_or_expectation`. Run only a project whose files Build
proved.

## Files

| File | Owner of |
|---|---|
| `data/policy.properties` | The rule parameters: `min_rest_hours` and `search_budget`. |
| `data/staff.csv` | The people and their contract. |
| `data/contracts.csv` | The maximum weekly hours of each contract. |
| `data/certifications.csv` | The certification kinds. |
| `data/staff_certifications.csv` | Who holds which certification, from which day, until which day. An empty `expires_on` is a missing expiry date. |
| `data/wards.csv` | The wards. |
| `data/shift_types.csv` | The start hour, the length and the required certification of each shift type. |
| `data/demand.csv` | For each ward and shift type: the minimum and maximum staff, the lead certification and the minimum number of lead holders. |
| `data/leave.csv` | Leave periods and their status. Only `approved` leave blocks a person. |
| `data/calendar.csv` | The plan days. This file is the clock of the plan: nothing reads the system time. |
| `lib/certificates.scr.py` | RS1: `certificate_status` and the enum `CertificateStatus`. |
| `lib/roster_search.scr.py` | The global search `plan_roster`. |
| `acceptance/build.json` | The roles, the input expectations, the rule expectations and the caller's edge controls. |
| `scenario.json` | What the corpus runner checks: the row counts and the negatives. |

## Policy

`data/policy.properties` is the one place for the rule parameters. The `policy` product of step 1 reads each value
once as a whole number. A value that is missing or not a whole number stops the run in step 1. Two checks limit the
values:

- `min_rest_hours >= 11`: a caller requirement. The specification asks for 11 hours of rest, so a smaller value is
  refused. A larger value is allowed.
- `search_budget >= 1`: an input expectation.

## Rules

| Rule | Decided in | Checked in the output | Parameter from |
|---|---|---|---|
| RS1 certification valid on the shift date | `certificate_status`, called by the `cert_status` key of `candidates` in step 3 | `cert_status == 'valid'` on `entry_checks` | `data/shift_types.csv` (`required_cert`), `data/staff_certifications.csv` |
| RS2 rest between two shifts, no overlap | `blocker` in `plan_roster` | `rest_hours == None or rest_hours >= min_rest_hours` on `entry_checks` | `data/policy.properties` (`min_rest_hours`) |
| RS3 weekly hours within the contract | `blocker` in `plan_roster` | `busiest_week_hours <= contract_hours` on `hours_checks` | `data/contracts.csv` |
| RS4 minimum and maximum staff, minimum lead holders | `solve` and `shortage` in `plan_roster` | `staffed >= min_staff and staffed <= max_staff`, `leads >= min_lead` on `coverage_checks` | `data/demand.csv` |
| RS5 one ward per day | `blocker` in `plan_roster` | `wards_that_day == 1` on `entry_checks`, a native `script=` count | the rule itself |
| RS6 never rostered on approved leave | the `on_leave` key of `candidates` in step 3 | `not on_leave` on `entry_checks`, the same filter stated again | `data/leave.csv` |

The output checks read the roster and the data again. They do not read the suitability decisions or the search evidence.
A rule that the search breaks is therefore caught, also when the search itself has a defect.
RS1 uses one function in suitability and in the output check. A defect in that function is caught only by the
caller's edge controls, not by the output check. RS6 is stated twice in XML, so the output check catches a suitability defect.

Definitions: a shift belongs to the day and the ISO week (year and week) of its start. It counts fully in that week,
also when it ends after midnight. "One ward per day" (RS5) uses the same start date.

## Edge controls

The caller requirements in `acceptance/build.json` name each edge with its ids. Each line below is one control.

| Edge | Data | Control |
|---|---|---|
| The expiry date is valid | S07 holds ALS until 2026-03-04 | S07 may work the night of 2026-03-04, not of 2026-03-05 |
| A missing expiry date is not valid | S09 holds ALS without an expiry date | S09 never works a night |
| The issue date is valid, the day before is not | The ALS of S06 starts on 2026-03-03 | S06 may work the night of 2026-03-03, not of 2026-03-02 |
| One valid holding is enough | S04 holds an expired ALS (listed first) and a valid ALS | S04 may work the night of 2026-03-02 |
| The first and the last leave day are leave days | S03 has approved leave from 2026-03-02 to 2026-03-04 | S03 is on leave on 2026-03-02 and 2026-03-04, not on 2026-03-05 |
| A requested leave does not block | S14 requested leave on 2026-03-05 | S14 may work the day shift of 2026-03-05 |
| Hours exactly at the contract maximum | S01 has the contract PT07 (7 h) and is the only Monday ICU+ALS holder | S01 works exactly 7 of 7 h |
| Only RS5 blocks a pair | S18 (BLS, 7 h contract) returns from leave on 2026-03-05 and takes the W1 evening. S03 works the W1 night: 11 h of rest before the W2 evening, and the fewest hours of the ICU holders | Without the RS5 check, the search gives S03 the W2 evening (negative `rs5_search_ignores_ward`). `slot_decisions` of `2026-03-05/W2/evening` shows S03 with `RS5` |
| Exactly the minimum rest is allowed | S03 works the W2 night and the W2 evening of 2026-03-07: 11 h of rest | The W2 evening of 2026-03-07 has `rest_hours == min_rest_hours` |
| Staff exactly at the slot maximum | The W1 evening needs 1 and allows 1 | W1 evening on 2026-03-02 is staffed at its maximum |
| The search needs a backtrack | see [Search](#search) | `backtracks >= 1` |

## Decision evidence

| Product | Content |
|---|---|
| `candidates` | One row for each person and plan day. `shifts` holds one decision for each shift type: `cert_status`, and `excluded_by` (`RS1`, `RS6` or empty). |
| `plan` | `outcome`, `search_complete`, `message`, `steps` and `backtracks`. |
| `slot_decisions` | For each slot: the assigned people, and for each other suitable person the strongest rule that excludes the person, given the shifts of the earlier slots, and the reason: `RS2` before `RS5` before `RS3`. `RS4` means that the slot has its maximum staff. `not_needed` means that no rule excludes the person: the slot has its minimum staff, and the search adds no more. |
| `entry_checks`, `hours_checks`, `coverage_checks` | The measured values that the rule expectations compare. |

The reasons in `slot_decisions` replay the plan slot by slot in search order. A reason sees only the shifts of the
earlier slots, never a later one. A choice that the search undid leaves no row: S01 shows `not_needed` on the W1 night
of 2026-03-02, although the search tried S01 there first. Only `plan.backtracks` shows that backtrack. The W2 night
shows its other half: S02 has `RS2`, because S02 now works the W1 night.


## Search

`plan_roster` staffs every slot at its minimum. It is a depth-first search with backtracking.

1. Sort the slots by start time, then by ward.
2. For each slot, try the teams of suitable people in a fixed order: fewest hours so far first, then by id.
3. After each choice, check that every later slot can still get its minimum staff and lead holders. If not, undo the choice (a backtrack).
4. Count each tried team as one step. Stop at `search_budget` steps.

The order is fixed, so the same inputs give the same plan. The first descent is the greedy pass.

**Backtracking case.** On Monday 2026-03-02 only S01 holds ICU and ALS: S03 is on leave, and the ALS of S05 and S06
starts on 2026-03-03. The greedy pass gives the W1 night shift to S01, who comes first. Then the W2 night shift has no
ICU lead. The search undoes this choice and gives W1 to S02.

**Outcomes.** They have different values and messages.

| `outcome` | `search_complete` | Meaning |
|---|---|---|
| `solved` | true | Every slot is staffed. |
| `infeasible` | true | No roster exists. The message names the slot and the shortage, or says that every team failed. |
| `budget_exhausted` | false | The search stopped at `search_budget` steps. This is not a proof that no roster exists. |

## Replay and seed

`rngSeed` is set, but nothing in this project is random: the search and the checks are fixed functions of the data.
The seed has no visible effect on the rows. It lets Build replay the run and compare every row, which is the replay
proof. The plan days come from `data/calendar.csv`, so the same model, data, seed and calendar give the same roster.

## Python

Python holds two things. `plan_roster` is the global search. `certificate_status` is RS1: suitability and the output
check call this one definition, because its five-way status is evidence in `candidates.csv`. Every other rule is a
`script=` filter in XML: RS6 in suitability and again in step 5, and the RS2 to RS5 output checks in step 5.

A library shares its names with the scripts. The libraries import the module `datetime`, not its classes:
the class `datetime` would hide the module `datetime` that the scripts use.
`CertificateStatus` and the search enums `Outcome` and `Rule` name the vocabularies (`Rule` also holds `not_needed`). A row holds their plain values,
so the XML conditions compare with the string `'valid'`. The search never reads a certificate status: it reads
`eligible_shifts` and `valid_certs`.

## Output

`datamimic run datamimic.xml` writes CSV files to `output/<random task id>/`. Each file has a header row, and the
delimiter is a comma (`defaultSeparator`). Steps 2 and 5 write their check products. Step 7 writes the 14 export files, named after the products they read (`roster.csv`,
`slot_decisions.csv`, and so on).

List and nested columns (`valid_certs`, `shifts`, `eligible_shifts`, `assigned`, `blocked`) hold Python literals,
not JSON: single quotes, `None`, `True` and `False`. Read them with Python `ast.literal_eval`.

When no roster exists, the run still ends with exit code 0. There is then no `roster.csv`, `entry_checks.csv` or
`slot_decisions.csv`, because these products have no rows. `plan.csv` holds the outcome and the message (#420).

## Change one parameter

1. Edit `data/policy.properties`, for example `search_budget=50`.
2. Run `datamimic authoring build tests_ce/scenarios/s13_shift_roster`.
3. Read `plan` for `outcome`, `steps` and `message`. At 50 steps the outcome is `budget_exhausted`.

A change of `min_rest_hours` also changes the roster. The edge control for the exact minimum rest then fails, because
it pins the 11 h rest of S03 on 2026-03-07.

## Cleanup

The cleanup step has nothing to delete. The CSV exporter writes a new output directory for each run, so no rows of an
earlier run remain. The step holds one `<echo>`, because Build refuses a step file that holds only a comment.
A database target needs a cleanup step that deletes the earlier rows after the output checks. A CE SQLite insert needs
an existing table, and Build refuses the SQL `execute` that creates it. For this reason this project uses CSV files.
The export is not a transaction: the files are written one after the other.

## Negatives

Each negative is one text patch in `scenario.json`: a file, an old text and a new text. The harness applies it to a
copy of the project and Builds the copy.

| Negative | What breaks |
|---|---|
| `rs1_certificate_ignored` | Suitability ignores the certification. |
| `rs1_expiry_exclusive` | The expiry date is read as exclusive. |
| `rs1_missing_expiry_unlimited` | A missing expiry date is read as valid. |
| `rs1_issue_date_ignored` | The issue date is ignored: a certification is valid before it starts. |
| `rs2_rest_ignored` | The assign step gives the search 0 hours of rest. |
| `rs3_over_contract` | One extra entry after the search: S13 works 36 h of 32 h. |
| `rs4_lead_ignored` | The assign step gives the search no lead requirement. |
| `rs4_over_max` | Two extra entries after the search: 3 people in a slot with a maximum of 2. |
| `rs5_search_ignores_ward` | The search does not check RS5. S03 then works the W1 night and the W2 evening of 2026-03-05. |
| `rs6_leave_ignored` | Suitability ignores the leave. |
| `rs6_leave_end_exclusive` | The last day of a leave is read as exclusive. |
| `infeasible_monday_lead` | S01 is on leave on Monday: no one can lead the W2 night shift. The check before the search proves it. |
| `infeasible_after_search` | The W1 night shift also needs an ICU lead. Each Monday night slot alone has a lead (S01), both together have not. The search tries every team. |
| `policy_not_whole` | `search_budget` is `ten`. Step 1 stops the run: Build reports `child_execution`, and a normal run fails with a `ValueError`. |
| `budget_exhausted` | `search_budget` is 50. |

When a negative changes the suitability or the lead requirement, the search does not need its backtrack.
Then the caller control `backtracks >= 1` also fails. This is not a second broken rule.
When no roster exists (the two infeasible negatives and `budget_exhausted`), the coverage checks and the controls on
the roster also fail. These are consequences of the empty roster, not more broken rules.
When a negative changes the plan, the `slot_decisions` pins can also fail: in `rs1_certificate_ignored`,
`rs1_issue_date_ignored`, `rs4_lead_ignored`, `rs5_search_ignores_ward` (the S03 `RS5` pin), `rs6_leave_ignored` and
`rs6_leave_end_exclusive`. These are consequences too.
A `slot_decisions` pin reads one index of `blocked`, because a row condition cannot search a list. Each pin also
checks the `staff_id` at its index. So an added person makes the pin fail, not pass. Then correct the index.

`scenario.json` names the `row_condition` that Build reports for each negative. The condition names the rule.
`outcome != 'infeasible'` fails only when no roster exists, and `search_complete == True` fails only when the search
stopped early. Together they mean `solved`. The two infeasible negatives share `outcome != 'infeasible'`: they prove
the same outcome on two paths, and `plan.message` shows which path.

## Warnings

Build reports two DM214 warnings: the `nestedKey` elements `shifts` (step 3) and `blocked` (step 4) have no
`defaultValue`. The rule asks for a fallback value when the script fails. This project accepts the warnings: a
fallback would hide a failure in the decision evidence. A failing script must stop the run.

## Known limits of this project

- The checks are a gate in Build only (see [Process](#process); F13, #420).
- There is no `delivery/` folder, and the cleanup step deletes nothing. A SQLite target needs an existing table, and Build refuses the
  SQL that creates it, so the project writes CSV files (F19, #420).
- RS1 is Python besides the search (see [Python](#python)). Its output check shares the suitability definition.
- The libraries import the module `datetime`, because a library name hides a script global of the same name (F3, #423).
- No shift in the data crosses midnight. With an evening shift from 20:00 for 8 hours, every rule check holds, but
  Build rejects the project: the rest edge on 2026-03-07 and the S03 `RS5` pin depend on the 18:00 evening.
- Build captures at most 1000 rows. See [Size](#size).

## Size

The brief asks for about 300 rows and 20 to 30 columns. The ten tables (nine data files and the roster) hold 135 rows
and 34 columns: 28 in the data files and 6 in the roster. That is 4 columns above the brief. Every column has a
reader, so the project keeps them.
The rows stay below the brief, because Build captures at most 1000 rows, and this project uses 822 of them. One more
person adds about 18 captured rows (candidates, checks and export readbacks). A second week doubles the slots, the
candidates and the roster, and goes above the limit.

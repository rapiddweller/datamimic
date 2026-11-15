# S47 course timetable (X3)

This project makes the timetable of five courses for one week. Each session gets a slot and a room. Students may
join a course only when they completed its prerequisite. All names and data are synthetic.

## Run the tests

```bash
pytest tests_ce/scenarios -q -k s47
datamimic authoring build tests_ce/scenarios/s47_course_timetable
```

The tests live in `tests_ce/scenarios/test_scenarios.py`. They Build, run and replay the project, and Build each negative.

## Process

```text
data/entity/*, conf/* ──> 10 prepare ──> 20 admission ──> 30 assign ──> 90 validate input ──> 91 validate output ──> 93 export
                          typed tables    T1, headcount    search T2..T6   input values          T1..T6 again          CSV files
```

| Step | File | Purpose |
|---|---|---|
| 10 prepare | `model/10_prepare.xml` | Read each data file and give each column its type. |
| 20 admission | `model/20_admission.xml` | Decide for each enrolment if the prerequisite is met (T1), and list the admitted students of each course. |
| 30 assign | `model/30_assign.xml` | Search for one complete timetable and keep the evidence of each decision. |
| 90 validate input | `delivery/90_validate_input.xml` | Measure room capacity and course sessions. Build compares them. |
| 91 validate output | `delivery/91_validate_output.xml` | Measure the timetable against every rule again, from the data. |
| 93 export | `delivery/93_export.xml` | Read each product back from the store and write it to CSV. |

The checks are a gate in Build only. A plain `datamimic run` exports a timetable that breaks a rule and ends with exit
code 0. Run only a project whose files Build proved. There is no cleanup step: a CSV export writes a new output
directory for each run.

## Files

| File | Owner of |
|---|---|
| `conf/policy.properties` | The rule parameter `search_budget`. A value that is not a whole number stops step 10. |
| `data/entity/slots.ent.csv` | The week: day and period of each slot. |
| `data/entity/rooms.ent.csv` | The rooms and their capacity. The smaller room comes first, so the search tries it first. |
| `data/entity/teachers.ent.csv`, `courses.ent.csv` | The teachers; the teacher, session count and prerequisite of each course. |
| `data/entity/students.ent.csv`, `completed.ent.csv`, `enrolments.ent.csv` | The students, the courses they completed, and their enrolment requests. |
| `data/entity/unavailable.ent.csv` | The slots in which a teacher cannot teach. |
| `lib/timetable_search.scr.py` | The global search `plan_timetable`. |
| `acceptance/build.json` | The roles, the input and rule expectations, and the caller's edge controls. |

## Rules

| Rule | Decided in | Checked in the output |
|---|---|---|
| T1 prerequisite completed | the `admitted` key of `enrolment_decisions` | `admitted == prerequisite_met` on `enrolment_checks` |
| T2 room capacity at least the admitted students | `refusal` in `plan_timetable` | `room_capacity >= headcount` on `session_checks` |
| T3 one session per teacher and slot, none in an unavailable slot | `refusal` | `teacher_sessions_in_slot == 1 and not teacher_off` |
| T4 one session per room and slot | `refusal` | `room_sessions_in_slot == 1` |
| T5 no student in two sessions of one slot | `refusal` | `student_clashes == 0` |
| T6 all sessions placed, one per day at most | `solve` and `refusal` | `sessions_planned == sessions_required`, `days == sessions_planned` on `course_checks` |

The output checks read the timetable and the data again. They do not read the search evidence, so a defect in the
search is caught too.

## Search

`plan_timetable` is a depth-first search with backtracking over the sessions (course id, then number).

1. For each session, try the places (slot, then room, in file order) that no rule refuses.
2. After each choice, check that every later session still has a place. If not, undo the choice (a backtrack).
3. Count each tried place as one step. Stop at `search_budget` steps.

The order is fixed, so the same inputs give the same timetable. With the data of this project the search needs 20
steps and 10 backtracks; the caller requirement `backtracks >= 1` pins this.

| `outcome` | `search_complete` | Meaning |
|---|---|---|
| `solved` | true | Every session is placed. |
| `infeasible` | true | No timetable exists. The message names the cause. |
| `budget_exhausted` | false | The search stopped at `search_budget` steps. This does not prove that no timetable exists. |

`session_decisions` holds, for each session, the places before the chosen one with the rule and the reason. `undone`
means that no rule refuses the place: the search tried it and undid the choice.

## Negatives

Each negative is one text patch in `scenario.json`. Build rejects the variant with a `row_condition` that names the rule.

| Negative | What breaks |
|---|---|
| `t1_prerequisite_ignored` | Every enrolment is admitted. |
| `t2_capacity_ignored`, `t3_*`, `t4_room_clash_ignored`, `t5_student_clash_ignored`, `t6_one_per_day_ignored` | The search ignores that rule. |
| `t6_session_dropped` | The search places one session less for each course. |
| `infeasible_five_sessions_four_days` | C101 needs 5 sessions on 4 days. |
| `budget_exhausted` | `search_budget` is 5. |
| `policy_not_whole` | `search_budget` is `ten`; step 10 stops (`child_execution`). |
| `room_without_seats`, `course_without_sessions` | An input value is not positive. |

## Known limits

- Build reports one DM214 warning: the `nestedKey` `skipped` has no `defaultValue`. A fallback would hide a failure in
  the decision evidence.
- Every product that goes to the store needs a readback and an identifier, so step 93 exports each of them.
- The search has no learning. It is exact for this size, but it grows fast: more courses or fewer slots need a higher
  `search_budget`.

# Step 100: align empty echo behavior

Base `008d4ce2`; published ArchKeel 0.8.5. Spec: the experiment
[protocol](protocol.md) and [Amendment 92](amendment-92.md).
Astra approved the diagnostic correction before implementation.

## Global constraints

Existing XML, oracle, baseline, budgets and gates remain unchanged.
No legacy paths, compatibility wrapper, EE or ArchKeel edits.
Root owns docs, Git and acceptance; agents never commit or spawn agents.
Independent QA owns tests; implementation owns only the two source files.

## Task 1: independent QA

Own `tests_ce/integration_tests/test_echo/test_echo.py` and ignored evidence.
Add a compact parameterized real-engine test using temporary XML: both empty
forms must complete and produce a later generated row. Assert empty debug
output; cover preserved whitespace and quoted interpolation. Reuse existing
normal and unresolved-placeholder tests rather than duplicate them.

- [x] Run the new test before production edits; empty forms must fail with
  the original `re.search` TypeError, not fixture/setup errors.
- [x] Wait for root's implementation gate, then verify the same tests green.
- [x] Run relevant echo tests, `make test-unit`, `make lint`, full
  `make typecheck`, and report warnings/skips/failures without hiding them.

## Task 2: independent implementation

Own `engine/runtime/tasks/flow/commands/echo_task.py` and
`engine/dsl/statements/flow/commands/echo_statement.py` under `datamimic_ce/`.
Independently inspect parser, dispatch and callers; wait for root's RED gate.

- [x] For a `None` value only, debug-log `Echo - ` and return.
- [x] Set `EchoStatement.value -> str | None` and `EchoTask.execute -> None`.
- [x] Leave nonempty execution and all other code unchanged; self-review.

## Acceptance

Root reruns echo and broader runtime suites, compares the same bounded DSL
captures and four Authoring projections, and verifies all XML bytes unchanged.
Fresh 0.8.5 observations should remove only EchoStatement's missing-return
UNKNOWN `00fd6d52c4ff0e12`; investigate actual deltas, never suppress evidence.
No new semantic findings or physical/dependency changes are permitted.
Astra reviews the complete diff and evidence before root commits/pushes to
Draft PR274. Final whole-goal, all-930 replay and report acceptance stay open.

# Amendment 166 — truthful native scope guidance

Date: 2026-10-08. Decision: Astra under Alex's delegation.
This amendment records an intentional public text change.

Change only `_SCOPE_GUIDANCE` in Runtime scripting evaluation and the three
ordinary literal message expectations. Current-scope names can resolve bare;
existing outermost bare names win collisions. Intermediate ancestor names need
qualification. Scope aliases apply only when available; qualified paths remain
supported. Keep prefixes, missing identifiers, exception classes/causes,
resolution, defaults, hint dispatch, `_SCOPE_HINT` and IPC unchanged.

Under protocol item 6, permit this suffix in native exceptions, logs/tracebacks
and public DM002 messages. This is not byte compatibility. The frozen historical
baseline at `3b844b5083e5af89269ef917bc0614601d30cf61` retains 19 old-suffix
messages: two EXPECTED-ERROR and 17 UNRUNNABLE. Preserve every row, oracle and
comparator; changed expected-error messages remain DIFFERENT and UNRUNNABLE
rows remain failed equivalence. No historical rewrite, normalization or waiver.

Acceptance requires literal-only RED/GREEN, unchanged diagnostic fields/hints,
existing native scope/assert owners and before/after native cause chains. Retain
actual message differences separately. A changed prefix, class or status stops
this slice. Downstream exact-string consumers and other affected paths remain
UNKNOWN. Step 131 clones/profile, architecture permissions and EE stay fixed.
Full DSL, equality, architecture and edition-local acceptance remain open.

## Local verification

- Test-first RED: three suffix-only assertion failures, four passing controls.
  Candidate: all 50 expression-evaluation and dry-run tests passed.
- Fresh detached clones at `0dd19653`: baseline clean; candidate changed only
  the approved evaluator literal. Four native scope owners and the broken-assert
  owner passed in both copies. This does not prove unseeded Person value parity.
- Direct captures of `assert_bad_expression.xml` and `nested_scope_reach_up.xml`
  retain `ValueError -> ValueError -> NameError`, names `ixd`/`mid`, cause/context
  relations and suppression flags. Only the approved suffix changes in native
  messages and arguments. Both historical messages match the baseline captures;
  the unchanged comparator rejects the observed new messages as DIFFERENT.
  This selected-message exercise is not a new full Step-0 snapshot.
- Source/input/data/dotenv/dependency pins, clone-local imports, fresh output
  containment and process cleanup passed. Only the approved Ray/SPT environment
  transitions occurred. Independent QA reviewed the profile, baseline and
  candidate pair, including the complete suffix-only cause/context comparison.
- Full-package Ruff and MyPy passed (491 source files). Changed-file Ruff passed;
  format-check failures reproduce identical pre-existing hunks in all three files.
- Architecture definition/structure tests: 12 passed. ArchKeel 1.0.0 observation
  PASS, declared rules FAIL: 89 violations, 200 measured UNKNOWN positions and
  58 baseline additions. No contract, baseline, comparator or EE changes.

CI-ONLY VERIFICATION: no new run at this checkpoint.

# Step 208 — six native while owner profiles

Independent native and docs/ledger SPEC/QUALITY GO admits six exact
input/isolation owner profiles: **180/931 reviewed, 751 UNKNOWN**. Root changes
only their new evidence statuses after the reviewed candidate. No source, tests, XML or contracts change.
[Receipt](step-208-native-while-receipt.json) pins the baseline, external candidate,
final review, controller, manifests, authorization and retained preparation proof.

Native endpoints are `a219163e533d661bcc7bda0faa5ecc77909ab5aa` and
`9e6667e105dcf436ccd15c334b977bc6442e390e`, **not primary
`b2da84901d957ff1339f7346afedd1bfe9d54085`**. Preflight verifies executable AST
bridges after removing only the reviewed `read_variable_query` and abstract
`BaseLiteralGenerator.generate` return annotations. Runtime annotation
introspection, external static consumers and primary b2 native parity remain UNKNOWN.

All six descriptors live in `tests_ce/integration_tests/test_while/`.

| Descriptor | Observed behavior at each endpoint |
|---|---|
| `while_counter.xml` | Three ordered integer `{n: 3, final: 3}` rows. |
| `while_compound_growth.xml` | Float balance `2143.5888100000006`, integer years `8`. |
| `while_luhn_next_valid.xml` | Two identical six-row captures; ordered string bases and integer PANs. |
| `while_cap.xml` | Exact `ValueError` for `max_iterations=5`, no cause/context. |
| `while_no_condition.xml` | Exact missing-condition `ValueError` and full Pydantic cause/context. |
| `while_empty_condition.xml` | Exact empty-condition `ValueError` and full Pydantic cause/context. |

The frozen runs contain **12 once-only owner calls, 14 engine instances and
executions, 8 captures, 32 rows, 6 engine-error graphs and 36 passing pytest
phases**. Complete values, native type trees, order and returned-object identity
agree. All non-traceback error-node fields agree, including messages and links;
distinct source-layout tracebacks match their own pinned origins. The cap owner
differs only by its stronger `ValueError` assertion, besides import relocation.

Captured phase stdout bytes agree; captured stderr agrees under frozen rules,
with cumulative teardown diagnostics retained. **Raw pytest runner stdout is
not byte-identical**: JUnit paths and durations differ. Raw runner stderr is empty.
No socket, process or worker-serialization audit events were observed. Audited
writes stay inside each owned child directory, apart from permitted `/dev/null`;
leaders are reaped and groups gone. This is bounded Python audit evidence, not
an OS sandbox or universal dependency/provider closure.

Failed preparation/collection attempts, deliberate cancellation and both
prelaunch refusals remain retained. Approved recovery uses the actual successful
collection launch context; no PATH/PWD/thread identity is transplanted.
**No phase-appropriate full verifier exists or passed.** Complete independent
direct preflight and final terminal raw review supply the bounded gates.

The external candidate changes exactly six rows: four existing input/isolation
fields plus new `native_while_owner_evidence`, whose status remains
`CANDIDATE_EXACT_OWNER_PROFILE` in the retained candidate. Root changes only these
six statuses to `ACCEPTED_EXACT_OWNER_PROFILE` in the separate accepted ledger.
The other **925 raw lines are byte-identical**;
historical, oracle and c992 fields stay exact. Candidate SHA256:
`a6f603a88c014460fc3bc86d42c35a2e1cae00b4f666cea1c37e14f4e03b885c`.
Raw evidence remains local under `/private/tmp/ce-step206-native-while-v2-20261010`,
not a durable CI artifact. These cases prove no new CE defect. Existing
[CE #293](https://github.com/rapiddweller/datamimic/issues/293) covers parser
`None` naming; fixes are separate.

Step 207's nested-source probe remains deferred and unintegrated. It neither
fixes the boundary nor proves a new checker bug. Current canonical architecture
remains **12 violations, 253 UNKNOWN records, 199 scalar positions**.

LOCAL VERIFIED: six exact candidate deltas, 925 unchanged raw lines, JSON and
18,988 native-manifest hashes, receipt pins, retained native totals, unchanged
primary/source/protected files, links and diff integrity; project Ruff and full
MyPy pass (488 files). No native code rerun.

CI-ONLY VERIFICATION: exact primary b2
[run 38078654656](https://github.com/rapiddweller/datamimic/actions/runs/38078654656)
is terminal: **24 successful jobs, two architecture failures, two skips**.
This is primary CI evidence, not native-packet or future documentation CI.
PR 274 remains Draft; full DSL/CE/EE target acceptance remains open.

Skipped runtime reruns, services, EE and duplicate unit-suite execution.
Risk: primary b2 runtime/introspection and full target acceptance remain unproved.
